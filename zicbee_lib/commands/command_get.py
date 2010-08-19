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
    all_filenames = set()
    dst_prefix = config.download_dir
    for infos in unroll(iter_webget(u) for u in memory['last_search']):
        if infos[-1] == '|':
            infos += ' '
        try:
            uri, artist, album, title = infos.split(' | ', 3)
        except ValueError:
            print repr(infos)
            import pdb; pdb.set_trace()
            raise
        ext = uri.rsplit('.', 1)[1].rsplit('?', 1)[0].strip()
        if len(ext) < 2:
            print "WARNING: Ext=%s for %s\n"%(ext, uri)
            ext = 'mp3'
        title = title.replace(os.path.sep, '-').split('\n', 1)[0]
        album = album.replace(os.path.sep, '-').split('\n', 1)[0]
        artist = artist.replace(os.path.sep, '-').split('\n', 1)[0]

        out_dir = os.path.join(dst_prefix.strip(), artist.strip(), album.strip())
        fname = os.path.join(out_dir, title.strip() or 'unknown') + "."
        if fname+ext in all_filenames:
            count = 1
            while True:
                new_name = "%s-%d%s"%(fname, count, ext)
                if new_name not in all_filenames:
                    fname = new_name
                    break
                count += 1
        else:
            fname += ext

        out_dir = os.path.dirname(fname)

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        to_download.append((uri, fname))
        all_filenames.add(fname)
    del all_filenames
    Downloader().run(to_download)
    output((e[1] for e in to_download))

