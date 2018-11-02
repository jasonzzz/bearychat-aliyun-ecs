#!/usr/bin/env python3

from tornado.options import options
import tornado.web, tornado.netutil, tornado.httpserver

from logs import Logs
from options import Options
from routers import Routers

if __name__ == "__main__":
    options = Options().init()

    Logs().init()

    routers = Routers(options['modules']).init()

    app = tornado.web.Application(routers, debug=True, autoreload=True)
#    socket = tornado.netutil.bind_unix_socket(options['socket'], mode=0o666)
#    tornado.httpserver.HTTPServer(app).add_socket(socket)
    app.listen(8001)

    tornado.ioloop.IOLoop.current().start()
