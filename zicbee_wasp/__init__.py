__version__='0.1-alpha'
def startup():
    import sys
    from .core import Shell, execute
    if len(sys.argv) > 1:
        execute(' '.join(sys.argv[1:]))
    else:
        s = Shell()
        s._prompt = 'wasp'
        s.cmdloop('Wasp %s!'%__version__)


