import os
import ConfigParser
import urllib as urllib2 # WARNING: urllib2 makes IncompleteRead sometimes...
import readline
from cmd import Cmd
from functools import partial
from .config import config_read, config_write, config_list, DB_DIR
from .downloader import Downloader

def _safe_webget_iter(uri):
    site = urllib2.urlopen(uri)
    while True:
        try:
            l = site.readline()
        except Exception, e:
            print "ERR:", e
            break
        else:
            if l:
                yield l.strip()
            else:
                break

def iter_webget(uri):
    if not '://' in uri:
        if 'db' in uri.split('/', 4)[:-1]:
            host = config_read('db_host')
        else:
            host = config_read('player_host')

        uri = 'http://%s/%s'%(host, uri.lstrip('/'))
    try:
        return _safe_webget_iter(uri)
    except IOError, e:
        print "webget(%s): %s"%(uri, e)

def webget(uri):
    i = iter_webget(uri)
    if i:
        return '\n'.join(i)

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

def modify_show(answers=10, start=None):
    if start:
        memory['show_offset'] = int(start)
        return '/playlist?res=%s&start=%s'%(answers, start)
    else:
        for line in iter_webget('/infos'):
            if line.startswith('pls_position'):
                start = line.split(':', 1)[1].strip()
                memory['now_playing'] = memory['show_offset'] = int(start)
                return '/playlist?res=%s&start=%s'%(answers, start)
        memory['show_offset'] = 0
        return '/playlist?res=%s'%(answers)

def tidy_show(it):
    offs = memory['show_offset']
    now = memory.get('now_playing', None)

    for i, line in enumerate(it):
        idx = offs+i
        print ('%3d '%idx if idx != now else ' >> ') + ' | '.join(line.split(' | ')[:4])

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

    try:
        pattern, doc = commands[name]
        extras = None
    except ValueError:
        pattern, doc, extras = commands[name]

    if callable(pattern):
        pattern = pattern(*args)
        if pattern is None:
            return

    args = [urllib2.quote(a) for a in args]

    if '%s' in pattern:
        expansion = tuple(args)
    else:
        expansion = dict(args = '%20'.join(args), db_host=config_read('db_host'), player_host=config_read('player_host'))
    try:
        uri = pattern%expansion
    except Exception, e:
        print "Invalid arguments: %s"%e
    else:
        if extras and extras.get('uri_hook'):
            extras['uri_hook'](uri)
        r = iter_webget(uri)
        if r:
            if extras and extras.get('display_modifier'):
                extras['display_modifier'](r)
            else:
                for line in r:
                    print line

# commands dict: <cmd name>:<request string OR handler_function>, <doc>, [extra dict]
# in request string, you can use two forms: positional or named
# in positional form, you should have as many %s as required parameters, they will be passed in given order
# in named form, you have dict expension for: args (a string containing all arguments separated by a space), db_host, player_host
# if given an handler_function, this is executed to get the request string
#
# In both forms, you should return an uri, if it's a relative prefix, db_host or player_host is chose according to "/db/" pattern presence
# the request result is print on the console
# TODO:
# in extra parameters, allow definition of a display_function

from time import time
class _LostMemory(dict):
    def __init__(self):
        self.amnesiacs = ('now_playing',)
        self._tss = dict()
        dict.__init__(self)

    def __getitem__(self, idx):
        if self._is_recent(idx):
            return dict.__getitem__(self, idx)

    def _is_recent(self, idx):
        if idx not in self.amnesiacs:
            return True
        DURATION=60
        t = time()
        return self._tss.get(idx, t) < t + DURATION

    def __setitem__(self, itm, val):
        self._tss[itm] = time()
        dict.__setitem__(self, itm, val)

    def __delitem__(self, slc):
        del self._tss[slc]
        dict.__delitem__(self, slc)

    def get(self, idx, default=None):
        if self._is_recent(idx):
            return dict.get(self, idx)

    def clear(self):
        dict.clear(self)
        self._tss.clear()

memory = _LostMemory()

def last_uri(u):
    memory['last_search'] = u

def get_last_search():
    uri = memory.get('last_search')
    if not uri:
        print "No previous search, use shell to re-use previous result!"
        return

    to_download = []
    for infos in iter_webget(memory['last_search']):
        uri, artist, album, title = infos.split(' | ', 4)
        ext = uri.rsplit('.', 1)[1].rsplit('?', 1)[0]
        if not os.path.exists(artist):
            os.mkdir(artist)
        out_dir = os.path.join(artist, album)
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        to_download.append((uri, os.path.join(out_dir, title) +"."+ext))
    Downloader().run(to_download)

commands = dict(
        play=('/search?host=%(db_host)s&pattern=%(args)s', 'Play a song', dict(uri_hook=last_uri)),
        search=('/db/search?fmt=txt&pattern=%(args)s', 'Query the database', dict(uri_hook=last_uri)),
        m3u=('/db/search?fmt=m3u&pattern=%(args)s', 'Query the database, request m3u format'),
        version=('/db/version', 'Show DB version'),
        db_tag=('/db/tag/%s/%s', 'Associates a tag to a song (params: Id, Tag)'),
        artists=('/db/artists', 'Show list of artists'),
        albums=('/db/albums', 'Show list of albums'),
        genres=('/db/genres', 'Show list of genres'),
        kill=('/db/kill', 'Power down'),
        get=(get_last_search, 'Download results of last search or play command'),
        set=(set_variables, 'List or set application variables'),
        # complete_set=(lambda: [v[0] for v in config_list()], lambda: set(v[1] for v in config_list()))
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
        playlist=('/playlist', "Shows the entire playlist (Might be SLOW!)"),
        show=(modify_show, "Shows N elements after the current song,\n you can optionally gives an alternative offset.", dict(display_modifier=tidy_show)),
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
        self._history = os.path.join(DB_DIR, 'wasp_history.txt')
        try:
            readline.read_history_file(self._history)
        except IOError:
            'First time you launch Wasp! type "help" to get a list of commands.'

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
        readline.set_history_length(int(config_read('history_size')))
        readline.write_history_file(self._history)
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


