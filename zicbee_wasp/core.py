from cmd import Cmd
import urllib2

class Cfg(dict):
    def __getattr__(self, name):
        return self[name]

config = Cfg(enable_history=False, default_port=9090, db_host='localhost', player_host='localhost', history_size=10)

def webget(uri):
    if not '://' in uri:
        uri = 'http://'+(uri.lstrip('/'))
    try:
        return urllib2.urlopen(uri).read()
    except IOError, e:
        print "webget(%s): %s"%(uri, e)

HOST='localhost:9090'

def execute(line):
    if line == 'help':
        for cmd, infos in commands.iteritems():
            print "%s : %s"%(cmd, infos[1])
        return
    args = line.split()
    name = args.pop(0)
    args = [urllib2.quote(a) for a in args]
    pattern, doc = commands[name]
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
        db_version=('/db/version', 'Show DB version'),
        db_tag=('/db/tag/%s/%s', 'Show DB version'),
        artists=('/db/artists', 'Show list of artists'),
        album=('/db/albums', 'Show list of albums'),
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
        show=('/playlist?res=%s', "Dumps N elements around the active playlist song"),
        guess=('/guess/%(args)s', "Tells if you are right (blind mode)"),
        shuffle=('/shuffle', "Shuffles the playlist"),
        tag=('/tag/%s', "Set a tag on current song"),
        rate=('/rate/%s', "Rate current song"),
#        clear=('/clear', "Empty the playlist"),
#        seek=('/seek/%s', "Seeks on current song"),
        )

class Shell(Cmd):
    def __init__(self, prompt='ZicBee'):
        Cmd.__init__(self)
        self._db_host = None
        self._player_host = None

        self.webget = webget

        self.history = dict(filename=None, value=[])
        if config.enable_history:
            try:
                history_file = os.path.join(DB_DIR, 'shell_history.txt')
                self.history['filename'] = history_file
                self.history['value'] = [l.rstrip() for l in file(history_file).readlines()]
                import readline
                for hist in self.history['value']:
                    readline.add_history(hist)
            except Exception, e:
                print "No history loaded: %s"%e
                self.history['value'] = []
        else:
            self.history['value'] = []

        self.commands = commands.keys()
        self._prompt = prompt
        self._refresh_prompt()

    def _refresh_prompt(self):
        ph = self._player_host
        dh = self._db_host

        local_hostname = ('localhost:%s'%config.default_port)

        if (ph is None and dh is None and config.db_host == config.player_host == local_hostname) or \
                (ph == dh == local_hostname):
            self.prompt = '[local]\n%s> '%self._prompt
        else:
            if ph != config.player_host:
                try:
                    if config.player_host.startswith('localhost:'):
                        raise Exception()
                    version = self.webget(config.player_host+'/db/version')
                except Exception:
                    self._player_host = config.player_host
                else:
                    self._player_host = "%s (%s)"%(config.player_host, version.strip() if version else '??')

            if dh != config.db_host:
                try:
                    if config.db_host.startswith('localhost:'):
                        raise Exception()
                    version = self.webget(config.db_host+'/db/version')
                except Exception:
                    self._db_host = config.db_host
                else:
                    self._db_host = "%s (%s)"%(config.db_host, version.strip() if version else '??')

            self.prompt = "[%s > %s]\n%s> "%(self._db_host, self._player_host, self._prompt)

    def get_names(self):
        return self.commands

    def onecmd(self, line):
        if not line:
            line = 'help'

        try:
            cmd, arg = line.split(None, 1)
        except:
            cmd = line
            arg = []
        else:
            arg = arg.split()
        self.lastcmd = line
        if cmd == '':
            return self.default(line)
        elif cmd in ('EOF', 'bye', 'exit', 'logout'):
            # save history & exit
            try:
                hist_fd = file(self.history['filename'], 'w')
                try:
                    hist_size = int(config.history_size)
                except ValueError:
                    hist_size = 100 # default value
                hist_fd.writelines("%s\n"%l for l in self.history['value'][-hist_size:])
            except Exception, e:
                print "Cannot save history file: %s."%(e)
            raise SystemExit('bye bye')
        else:
            return execute(line)
