import logging, json, time, os
from logging import handlers

class BufferingLogHandler(logging.handlers.BufferingHandler):
    def __init__(self, capacity):
        logging.handlers.BufferingHandler.__init__(self, capacity)

    def flush(self):
        buffer = []
        if len(self.buffer) > 0:
            try:
                print("I am superflushed:", self.buffer)
            except:
                self.handleError(None)  # no particular record
            buffer = self.buffer
            self.buffer = []
        return(buffer)
