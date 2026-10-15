# FILE          : logger_service.py
# PROJECT       : SENG2045 - Assignment 2 - Services and Logging
# PROGRAMMER    : Ansh Patel (apatel7102) | Khush Patel (kpatel19724)
# FIRST VERSION : 2026-10-09
# DESCRIPTION   : This is a network logging service that listens for TCP connections from multiple clients at the same time. 
#                 It takes all their log messages and saves them into one plain-text file. To keep track of who sent what, it identifies each
#                 client by their unique IP address and port.


import json
import sys

#
# FUNCTION      : main
# DESCRIPTION   : loads the config file named on the command line.
# PARAMETERS    : None
# RETURNS       : int
def main():
    if len(sys.argv) != 2:
        print("Usage: python3 logger_service.py <config_file>", file=sys.stderr)
        return 1

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, ValueError) as startup_error:
        print("Startup error: " + str(startup_error), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
