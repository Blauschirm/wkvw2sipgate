#!/usr/bin/python


import os
import socket

import tornado.httpserver
import tornado.ioloop
import tornado.web

port = 8888
debug = True

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"), 
}

class MainHandler(tornado.web.RequestHandler):
    def check_origin(self, origin):
        return True
    def get(self):
        self.render("static/index.html")

def StartServer(port):
    http_server = tornado.httpserver.HTTPServer(Application)
    http_server.listen(port)
    myIP = socket.gethostbyname(socket.gethostname())
    if debug: print('*** Server Started at {0}:{1}***'.format(myIP, port))
    tornado.ioloop.IOLoop.instance().start()
    if debug: print("Server stopped.")

Application = tornado.web.Application([
    (r"/", MainHandler)
], **settings)

if __name__ == "__main__":
    print("Starting")    
    StartServer(port)