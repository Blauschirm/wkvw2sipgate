#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import required modules
import time
import sys

# path and name of the log file
logfile = '/var/log/logfile.log'

# function to save log messages to specified log file
def log(msg):

  # open the specified log file
  file = open(logfile,"a")

  # write log message with timestamp to log file
  file.write("%s: %s\n" % (time.strftime("%d.%m.%Y %H:%M:%S"), msg))

  # close log file
  file.close

# main function
def main():
  # create new log message
  log("Eine neue Nachricht für die Log-Datei")

  # quit python script
  sys.exit(0)