# FILE          : logger_service.py
# PROJECT       : SENG2045 - Assignment 2 - Services and Logging
# PROGRAMMER    : Ansh Patel (apatel7102) | Khush Patel (kpatel19724)
# FIRST VERSION : 2026-10-09
# DESCRIPTION   : This is a network logging service that listens for TCP connections from multiple clients at the same time. 
#                 It takes all their log messages and saves them into one plain-text file. To keep track of who sent what, it identifies each
#                 client by their unique IP address and port


import json
import socketserver
import sys
import threading
from datetime import datetime
import time
from collections import deque

# A message line which has the exactly three parts  level, app name, message
FIELD_SEPARATOR = "|"
FIELD_COUNT = 3

# CLASS         : LogWriter
# DESCRIPTION   : Has the responsibilities for a single log file. Formats each entry to use the configured
#                 template and appends it. A lock prevents simultaneous clients from interfering with each other's lines
#
class LogWriter:

    #
    # FUNCTION      : __init__
    # DESCRIPTION   : Opens or creates the log file in append mode
    # PARAMETERS    : log_file_path str 
    #                 log_format str    
    # RETURNS       : none
    #
    def __init__(self, log_file_path, log_format):
        self.log_format = log_format
        self.write_lock = threading.Lock()
        self.log_file = open(log_file_path, "a", encoding="utf-8")

    #
    # FUNCTION      : format_entry
    # DESCRIPTION   : Builds one log line from the configured template
    # PARAMETERS    : level str, client_ip str, client_port int,
    #                 app str, message str
    # RETURNS       : str  the formatted log line
    #
    def format_entry(self, level, client_ip, client_port, app, message):
        timestamp = datetime.now().astimezone().isoformat(timespec="milliseconds")
        return self.log_format.format(
            timestamp=timestamp,
            level=level,
            client_ip=client_ip,
            client_port=client_port,
            app=app,
            message=message,
        )

    #
    # FUNCTION      : write_entry
    # DESCRIPTION   : formats one entry and adds it to the log file
    # PARAMETERS    : level str, client_ip str, client_port int,
    #                 app str, message str
    # RETURNS       : none
    #
    def write_entry(self, level, client_ip, client_port, app, message):
        log_line = self.format_entry(level, client_ip, client_port, app, message)
        with self.write_lock:
            self.log_file.write(log_line + "\n")
            self.log_file.flush()

# CLASS         : RateLimiter
# DESCRIPTION   : sliding-window rate limiter for one client Allows at most
#                 max_messages within any window of window_seconds
#
class RateLimiter:

    #
    # FUNCTION      : __init__
    # DESCRIPTION   : Sets up an empty window of message times
    # PARAMETERS    : max_messages int, window_seconds float
    # RETURNS       : none
    #
    def __init__(self, max_messages, window_seconds):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_times = deque()

    #
    # FUNCTION      : is_allowed
    # DESCRIPTION   : Records a message attempt and says whether it is within
    #                 the limit
    # PARAMETERS    : none
    # RETURNS       : bool  True if the message may be logged
    #
    def is_allowed(self):
        now = time.monotonic()
        window_start = now - self.window_seconds

        while self.message_times and self.message_times[0] < window_start:
            self.message_times.popleft()

        if len(self.message_times) >= self.max_messages:
            return False

        self.message_times.append(now)
        return True

# CLASS         : LogClientHandler
# DESCRIPTION   : Its own thread handles the client connection and apply the rate limiting and 
#                 validate the each message and logs the valid ones and replies to each message

class LogClientHandler(socketserver.StreamRequestHandler):

    #
    # FUNCTION      : handle
    # DESCRIPTION   : main loop for one client connection
    # PARAMETERS    : none
    # RETURNS       : none
    #
    def handle(self):
        client_ip, client_port = self.client_address[0], self.client_address[1]
        for raw_line in self.rfile:
            line = raw_line.decode("utf-8").rstrip("\r\n")
            error_reason, level, app, message = self.parse_message(line)
            if error_reason:
                self.send_reply("ERROR: " + error_reason)
                continue
            self.server.log_writer.write_entry(level, client_ip, client_port, app, message)
            self.send_reply("OK")

#Added a function name parse message(), which divides each line on | into level , app name and messages .If the lines are without this structure can get the error message"
    # FUNCTION      : parse_message
    # DESCRIPTION   : splits a line into level, app name and message and
    #                 checks each part
    # PARAMETERS    : line (str) 
    # RETURNS       : error_reason, level, app, message
    #                 
    #
    def parse_message(self, line):
        fields = line.split(FIELD_SEPARATOR, FIELD_COUNT - 1)
        if len(fields) != FIELD_COUNT:
            return "expected LEVEL|app_name|message", None, None, None

        level = fields[0].strip()
        app = fields[1].strip()
        message = fields[2].strip()

        if level not in self.server.config["allowed_levels"]:
            return "unknown level '" + level + "'", None, None, None
        if not app:
            return "app name is empty", None, None, None
        if not message:
            return "message is empty", None, None, None

        return None, level, app, message

    #
    # FUNCTION      : send_reply
    # DESCRIPTION   : sends one reply line to the client
    # PARAMETERS    : reply 
    # RETURNS       : none
    #
    def send_reply(self, reply):
        self.wfile.write((reply + "\n").encode("utf-8"))
        self.wfile.flush()


#
# CLASS         : LoggingServer
# DESCRIPTION   : TCP server , in this each client can executes in its own thread so multiple 
#                 clients can log at the same time
#
class LoggingServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    #
    # FUNCTION      : __init__
    # DESCRIPTION   : Binds the server and keeps the shared config
    # PARAMETERS    : config (dict)
    # RETURNS       : none
    #
    def __init__(self, config, log_writer):
        self.config = config
        self.log_writer = log_writer
        super().__init__((config["host"], config["port"]), LogClientHandler)

#
# FUNCTION      : main
# DESCRIPTION   : loads the config file named on the command line
# PARAMETERS    : None
# RETURNS       : int
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 logger_service.py <config_file>", file=sys.stderr)
        return 1

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            log_writer = LogWriter(config["log_file"], config["log_format"])
            log_writer.format_entry("INFO", "0.0.0.0", 0, "app", "test")    # test the log format string
            server = LoggingServer(config, log_writer)
    except (OSError, ValueError, KeyError) as startup_error:
        print("Startup error: " + str(startup_error), file=sys.stderr)
        return 1

    print(f"Listening on {config['host']}:{config['port']}, logging to {config['log_file']}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
