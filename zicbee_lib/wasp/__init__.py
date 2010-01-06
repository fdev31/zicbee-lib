def startup():
    import sys
    from .core import Shell
    from zicbee_lib import commands, __version__ as VERSION
    if len(sys.argv) > 1:
        from zicbee_lib.commands import execute
        commands.ALLOW_ASYNC = False
        commands.execute(' '.join(sys.argv[1:]))
    else:
        s = Shell()
        s._prompt = 'wasp'
        user_happy = True
        while user_happy:
            try:
                s.cmdloop('Wasp %s!'%VERSION)
            except KeyboardInterrupt:
                if raw_input("Do you really want to exit (y/n) ? ").lower()[:1] == 'y':
                    user_happy = False


