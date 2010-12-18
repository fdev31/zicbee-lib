""" pkg_resources-like functions, may use pkg_resources directly """

__all__ = ['get_players', 'resource_filename', 'set_proc_title']

from pkg_resources import iter_entry_points, resource_filename

def get_players():
    """ returns an iterable with available Player classes """
    return iter_entry_points("zicbee.player")

def set_proc_title(name):
    """ Sets the process name on the OS

    :arg str name: the name we would like
    """
    try:
        import setproctitle
        setproctitle.setproctitle(name)
        return True
    except:
        return
