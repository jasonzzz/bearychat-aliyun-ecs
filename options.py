import sys

from tornado.options import OptionParser, Error

class Options(OptionParser):
    def define(self, name, default=None, type=None, help=None, metavar=None,
               multiple=False, group=None, callback=None, required=False):
        super().define(name, default, type, help, metavar, multiple, group, callback)
        self._options[name].required = required

    def parse_command_line(self, args=None, final=True):
        # from tornado.options v4.4.1
        if args is None:
            args = sys.argv
        remaining = []
        for i in range(1, len(args)):
            # All things after the last option are command line arguments
            if not args[i].startswith("-"):
                remaining = args[i:]
                break
            if args[i] == "--":
                remaining = args[i + 1:]
                break
            arg = args[i].lstrip("-")
            name, equals, value = arg.partition("=")

            name = self._normalize_name(name)
            if name not in self._options:
                self.print_help()
                raise Error('Unrecognized command line option: %r' % name)

            option = self._options[name]
            if not equals:
                if option.type == bool:
                    value = "true"
                else:
                    raise Error('Option %r requires a value' % name)
            option.parse(value)

        # check required
        for name in self._options.keys():
            if self._options[name].required is True and len(self._options[name].value()) == 0:
                self.print_help()
                raise Error('Required command line option: %r' % name)

        if final:
            self.run_parse_callbacks()

        return remaining

    def rules(self):
        self.define('modules', required=True, multiple=True,
                    help='modular handlers, seperated by comma')
        self.define('socket', default='/tmp/webhook.socket',
                    help='specify socket file')

    def init(self):
        self.rules()
        self.parse_command_line()

        return self
