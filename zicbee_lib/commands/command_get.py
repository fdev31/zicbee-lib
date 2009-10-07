import os
from zicbee_lib.downloader import Downloader
from zicbee_lib.core import iter_webget, memory

def get_last_search(output):
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
    output((e[1] for e in to_download))

