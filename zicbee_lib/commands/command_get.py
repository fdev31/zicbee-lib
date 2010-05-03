import os
from zicbee_lib.downloader import Downloader
from zicbee_lib.core import iter_webget, memory
from zicbee_lib.config import config
from zicbee_lib.commands import unroll

def get_last_search(output):
    uris = memory.get('last_search')
    if not uris:
        print "No previous search, use shell to re-use previous result!"
        return

    to_download = []
    dst_prefix = config.download_dir
    for infos in unroll(iter_webget(u) for u in memory['last_search']):
        uri, artist, album, title = infos.split(' | ', 4)
        ext = uri.rsplit('.', 1)[1].rsplit('?', 1)[0]
        out_dir = os.path.join(dst_prefix, artist, album)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        to_download.append((uri, os.path.join(out_dir, title) +"."+ext))
    Downloader().run(to_download)
    output((e[1] for e in to_download))

