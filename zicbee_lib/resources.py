__all__ = ['get_players', 'resource_filename']

from pkg_resources import iter_entry_points, resource_filename

def get_players():
    """ returns an iterable with available Player classes """
    return iter_entry_points("zicbee.player")

