from cmd import Cmd
import ConfigParser
import urllib2
from functools import partial
from .config import config_read, config_write, config_list

def webget(uri):
    if not '://' in uri:
        uri = 'http://%s/%s'%(config_read('db_host'), uri.lstrip('/'))
    try:
        return urllib2.urlopen(uri).read()
    except IOError, e:
        print "webget(%s): %s"%(uri, e)

def show_help(name):
    print commands[name][1]

def set_variables(name=None, value=None):
    try:
        if name is None:
            for varname, varval in config_list():
                print "%s = %s"%(varname, varval)
        elif value:
            config_write(name, value)
            print "%s = %s"%(name, config_read(name))
        else:
            print config_read(name)
            print "%s = %s"%(name, config_read(name))
    except ConfigParser.NoOptionError:
        print "invalid option."

def modify_show(start=None, answers=10):
    if start:
        return '/playlist?res=%s&start=%s'%(answers, start)
    else:
        for line in webget('/infos').split('\n'):
            if line.startswith('pls_position'):
                start = line.split(':', 1)[1].strip()
                return '/playlist?res=%s&start=%s'%(answers, start)
        return '/playlist?res=%s'%(answers)

def execute(name=None, line=None):
    if line is None:
        args = name.split()
        name = args.pop(0)
    else:
        args = line.split()

    if name == 'help':
        for cmd, infos in commands.iteritems():
            print "%s : %s"%(cmd, infos[1])
        return

    pattern, doc = commands[name]
    if callable(pattern):
        pattern = pattern(*args)
        if pattern is None:
            return

    args = [urllib2.quote(a) for a in args]

    if '%s' in pattern:
        expansion = tuple(args)
    else:
        expansion = dict(args = '%20'.join(args))
    uri = pattern%expansion
    print webget(uri)

commands = dict(
        play=('/search?pattern=%(args)s', 'Play a song'),
        search=('/db/search?fmt=txt&pattern=%(args)s', 'Query the database'),
        m3u=('/db/search?fmt=m3u&pattern=%(args)s', 'Query the database, request m3u format'),
        version=('/db/version', 'Show DB version'),
        db_tag=('/db/tag/%s/%s', 'Associates a tag to a song (params: Id, Tag)'),
        artists=('/db/artists', 'Show list of artists'),
        albums=('/db/albums', 'Show list of albums'),
        genres=('/db/genres', 'Show list of genres'),
        kill=('/db/kill', 'Power down'),
        set=(set_variables, 'List or set application variables'),
        stfu=('/close', 'Closes player'),
        # TODO: get, will download last search/play using db/get/song.mp3?id=<id>
        pause=('/pause', 'Toggles pause'),
        next=('/next', 'Zap current track'),
        prev=('/prev', 'Go back to last song'),
        infos=('/infos', 'Display player status'),
        meta=('/db/infos?id=%s', 'Display metadatas of a song giving his id'),
        delete=('/delete?idx=%s', "Remove player's song at given position"),
        move=('/move?i1=%s&i2=%s', "Move a song from a position to another"),
        append=('/append?name=%s', "Append a named playlist to the current playlist"),
        save=('/copy?name=%s', "Save the current playlist as given name"),
        volume=('/volume?val=%s', "Changes the volume"),
        playlist=('/playlist', "Dumps the playlist"),
#        show=('/playlist?res=10&start=%s', "Dumps N elements around the active playlist song"),
        show=(modify_show, "Dumps N elements around the active playlist song"),
        guess=('/guess/%(args)s', "Tells if you are right (blind mode)"),
        shuffle=('/shuffle', "Shuffles the playlist"),
        tag=('/tag/%s', "Set a tag on current song"),
        rate=('/rate/%s', "Rate current song"),
        clear=('/clear', "Flushes the playlist"),
#        seek=('/seek/%s', "Seeks on current song"),
        )

class Shell(Cmd):
    prompt = "Wasp> "
    def __init__(self):

        for cmd, infos in commands.iteritems():
            setattr(self, 'do_%s'%cmd, partial(execute, cmd))
            setattr(self, 'help_%s'%cmd, partial(show_help, cmd))
        Cmd.__init__(self)
        self.names = [n for n in dir(self) if n.startswith('do_') and callable(getattr(self, n))]

    def onecmd(self, line):
        if len(line.split()) == 1 and line not in commands.keys():
            possible_keys = [k for k in commands.keys() if k.startswith(line)]
            if len(possible_keys) <= 1:
                return Cmd.onecmd(self, possible_keys[0] if possible_keys else line)
            else:
                print "Ambiguity: %s"%(', '.join(possible_keys))
                return
        return Cmd.onecmd(self, line)

    def complete_set(self, cur_var, line, s, e):
        params = line.split()
        ret = None
        if len(params) <= 2:
            ret = (v for v, a in config_list() if v.startswith(cur_var))
        elif len(params) > 2:
            ret = set([v[1] for v in config_list()] + ['localhost'])

        return [cur_var+h[e-s:] for h in ret if h.startswith(cur_var)]

    def get_names(self):
        return self.names

    def do_EOF(self, line):
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


