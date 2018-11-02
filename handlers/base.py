from tornado.web import RequestHandler

class BaseHandler(RequestHandler):
    def head(self):
        self.set_status(405)

    def write_error(self, status_code, **kwargs):
        self.write(str(status_code))

    def is_authorized(self, t):
        token = ''
        return t == token
