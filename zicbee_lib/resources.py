__all__ = ['get_players', 'resource_filename', 'set_proc_title']

from pkg_resources import iter_entry_points, resource_filename

def get_players():
    """ returns an iterable with available Player classes """
    return iter_entry_points("zicbee.player")

def set_proc_title(name):
    try:
        import setproctitle
        setproctitle.setproctitle(name)
        return True
    except:
        return
