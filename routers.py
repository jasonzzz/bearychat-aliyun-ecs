from handlers import aliyun

class Routers:
    def __init__(self, handlers):
        self.routers = []
        self.handlers = handlers

    def init(self):
        for handler in self.handlers:
            # FIXME: import modules dynamically
            self.routers += getattr(self, handler)()

        return self.routers

    # modular routers
    def aliyun(self):
        return [(r'/aliyun', aliyun.AliyunHandler)]
