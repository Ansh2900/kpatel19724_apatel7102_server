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
        for raw_line in self.rfile:
            self.send_reply("OK")

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
    def __init__(self, config):
        self.config = config
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
            server = LoggingServer(config)
    except (OSError, ValueError, KeyError) as startup_error:
        print("Startup error: " + str(startup_error), file=sys.stderr)
        return 1

    print(f"Listening on {config['host']}:{config['port']}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
