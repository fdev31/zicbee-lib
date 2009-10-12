__all__ = ['get_players', 'resource_filename']

import pkg_resources
def get_players():
    """ returns an iterable with available Player classes """
    return pkg_resources.iter_entry_points("zicbee.player")

def resource_filename(package, resource):
    """ substitute to pkg_resources.resource_filename """
    return pkg_resources.resource_filename(package, resource)

