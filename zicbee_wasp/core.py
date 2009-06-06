from cmd import Cmd
import urllib2
from functools import partial

HOST='localhost:9090'

def webget(uri):
    if not '://' in uri:
        uri = 'http://'+(uri.lstrip('/'))
    try:
        return urllib2.urlopen(uri).read()
    except IOError, e:
        print "webget(%s): %s"%(uri, e)

def show_help(name):
    print commands[name][1]

def modify_show(start=None, answers=10):
    if start:
        return '/playlist?res=%s&start=%s'%(answers, start)
    else:
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

    args = [urllib2.quote(a) for a in args]

    if '%s' in pattern:
        expansion = tuple(args)
    else:
        expansion = dict(args = '%20'.join(args))
    uri = HOST+(pattern%expansion)
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

    def get_names(self):
        return self.names

    def do_EOF(self, line):
        raise SystemExit()

    do_exit = do_quit = do_bye = do_EOF


