""" main function used in Wasp """
import os
import readline
from cmd import Cmd
from functools import partial
from zicbee_lib.commands import commands, execute
from zicbee_lib.resources import set_proc_title
from zicbee_lib.config import config, DB_DIR
from zicbee_lib.debug import DEBUG


def complete_command(name, completer, cur_var, line, s, e):
    """ Generic completion helper """
    ret = completer(cur_var, line.split())
    return [cur_var+h[e-s:] for h in ret if h.startswith(cur_var)]

class Shell(Cmd):
    """ Wasp shell :) """

    #: default prompt
    prompt = "Wasp> "

    def __init__(self):
        self._history = os.path.join(DB_DIR, 'wasp_history.txt')
        self._last_line = None
        try:
            readline.read_history_file(self._history)
        except IOError:
            'First time you launch Wasp! type "help" to get a list of commands.'

        for cmd, infos in commands.iteritems():
            try:
                completer = commands[cmd][2]['complete']
            except (IndexError, KeyError):
                pass # no completor
            else:
                setattr(self, 'complete_%s'%cmd, partial(complete_command, cmd, completer))
        Cmd.__init__(self)
        print "Playing on http://%s songs from http://%s/db"%(config['player_host'][0], config['db_host'][0])
        self.names = ['do_%s'%c for c in commands.keys()] + ['do_help']
        set_proc_title('wasp')

    def onecmd(self, line):
        """ Executes one line
        :arg str line: the line to execute
        """
        try:
            cmd, arg, line = self.parseline(line)
            if not line:
                return self.emptyline()
            if cmd is None:
                return self.default(line)
            self.lastcmd = line
            if cmd == '':
                ret = self.default(line)
            else:
                ret = execute(cmd, arg)
        except Exception, e:
            print "Err: %s"%e
            DEBUG()
        except KeyboardInterrupt:
            print "Interrupted!"
        else:
            print "."
            return ret

    def get_names(self):
        """ Returns the list of commands """
        return self.names

    def do_EOF(self, line):
        """ Handles EOF user-event """
        try:
            readline.set_history_length(int(config['history_size']))
        except:
            pass

        readline.write_history_file(self._history)
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


