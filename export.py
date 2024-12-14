#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>
#

# export.py
# ---------

import logging
import sqlite3
import os.path
import re
import sys
import shutil
import pathlib
import unicodedata
import subprocess
import ffmpy
import itertools

from unidecode import unidecode

logger = logging.getLogger(__name__)

EXPORT_FOLDER=pathlib.Path('/home/raskolnikov/sync/music-export')
EXPORT_FOLDER_COMPAT=pathlib.Path('/home/raskolnikov/sync/music-export')

class Settings:
    # When compat is True, we will convert files to mp3 for
    # compatibility with older players
    compat = False
    path = None
    tracks = None
    plists = None
    def __init__(self, compat = False):
        self.compat = compat
        self.path = EXPORT_FOLDER_COMPAT if compat else EXPORT_FOLDER
        self.tracks = self.path / 'tracks'
        self.plists = self.path / 'playlists'
        self.tracks.mkdir(parents=True, exist_ok=True)
        self.plists.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename):
    """Return a fairly safe version of the filename.

    We don't limit ourselves to ascii, because we want to keep municipality
    names, etc, but we do want to get rid of anything potentially harmful,
    and make sure we do not exceed Windows filename length limits.
    Hence a less safe blacklist, rather than a whitelist.
    """
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]  # Reserved words on Windows
    filename = "".join(c for c in filename if c not in blacklist)
    # Remove all charcters below code point 32
    filename = "".join(c for c in filename if 31 < ord(c))
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.rstrip(". ")  # Windows does not allow these at end
    filename = filename.strip()
    if all([x == "." for x in filename]):
        filename = "__" + filename
    if filename in reserved:
        filename = "__" + filename
    if len(filename) == 0:
        filename = "__"
    if len(filename) > 255:
        parts = re.split(r"/|\\", filename)[-1].split(".")
        if len(parts) > 1:
            ext = "." + parts.pop()
            filename = filename[:-len(ext)]
        else:
            ext = ""
        if filename == "":
            filename = "__"
        if len(ext) > 254:
            ext = ext[254:]
        maxl = 255 - len(ext)
        filename = filename[:maxl]
        filename = filename + ext
        # Re-check last character (if there was no extension)
        filename = filename.rstrip(". ")
        if len(filename) == 0:
            filename = "__"
    return filename

def create_playlist(filenames):
    """Create a PLS playlist from filenames."""
    yield '[playlist]\n\n'
    num = 0
    entry = (
        'File%d=%s\n'
        'Title%d=%s\n'
        'Length%d=-1\n\n'
    )
    for filename in filenames:
        num += 1
        title = os.path.splitext(os.path.basename(filename))[0]
        yield entry % (num, filename, num, title, num)

    yield (
        'NumberOfEntries=%d\n'
        'Version=2\n'
    ) % num

def export_file(settings, db, tid, file_db):
    # if we already copied this file, just return the target location
    if ('track', tid) in file_db:
        logger.debug("already exported: %s, %s", tid, file_db[('track', tid)])
        return file_db[('track', tid)]

    # otherwise copy the file and return the resulting filename
    location, artist, title, bpm = db.execute('''
      SELECT location, artist, title, bpm
      FROM library
      WHERE id=?
    ''', (tid,)).fetchone()
    path_str, = db.execute('''
      SELECT location
      FROM track_locations
      WHERE id=?
    ''', (location,)).fetchone()

    logger.debug("exporting track: %s, \"%s\"", tid, path_str)

    # https://github.com/syncthing/syncthing/blob/8f8e8a92858ebb285fada3a09b568a04ec4cd132/lib/protocol/nativemodel_darwin.go#L8
    # https://stackoverflow.com/questions/3194516/replace-special-characters-with-ascii-equivalent
    src_file = pathlib.Path(path_str)
    dst_ext = ".mp3" if settings.compat else src_file.suffix
    dst_file = settings.tracks / sanitize_filename(unidecode(
        '__'.join([
            "%g" % (attr,) if isinstance(attr, float) else str(attr)
            for attr in [artist, title, bpm, tid]
            if bool(attr)
        ]) + dst_ext
    ))
    logger.debug("copying:\n  %s\n  %s", src_file, dst_file)

    if dst_file.exists() and (
            settings.compat or src_file.stat().st_size == dst_file.stat().st_size
    ):
        logger.debug("file already exists: %s", dst_file)
    else:
        try:
            if settings.compat and src_file.suffix.lower() != ".mp3":
                logger.info("converting: %s", dst_file)
                ffmpy.FFmpeg(
                    inputs={src_file: '-err_detect ignore_err'}, # add -nv when file breaks
                    outputs={dst_file: '-b:a 320k -ignore_unknown '
                             + ('-metadata artist="' + artist + '" ' if artist else '')
                             + ('-metadata title="' + title +'"' if title else '')},
                ).run()
            else:
                shutil.copyfile(src_file, dst_file)
        except FileNotFoundError:
            logger.warning("file not found: %s", src_file)
        except:
            logger.error("error while copying file: %s", dst_file)
            try:
                os.remove(dst_file)
            except:
                pass
            raise

    file_db[('track', tid)] = dst_file
    return dst_file


def save_file(fname, content):
    with open(fname, 'w') as f:
        for txt in content:
            f.write(txt)


def export_playlist(settings, db, pid, name, file_db):
    if ('plist', pid) in file_db:
        logger.error("duplicate plist: %s (%s)", pid, name)
        return file_db['plist', pid]

    tracks = db.execute('''
      SELECT track_id, position
      FROM PlaylistTracks
      WHERE playlist_id=?
      ORDER BY position
    ''', (pid,))
    playlist_file = settings.plists / ("%s.pls" % name)
    logger.info("exporting playlist: %s", playlist_file)

    files = [
        '..' / export_file(settings, db, tid, file_db).relative_to(settings.path)
        for tid, tpos in tracks
    ]
    playlist = create_playlist(files)
    save_file(playlist_file, playlist)
    file_db[('plist', pid)] = playlist_file
    return playlist_file


def main(compat = False):
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    db = sqlite3.connect('./mixxxdb.sqlite')
    settings = Settings(compat)
    old_files = [
        f for f in itertools.chain(
            settings.tracks.iterdir(),
            settings.plists.iterdir())
        if f.is_file()
    ]
    file_db = {}

    playlists = db.execute('''
      SELECT id, name
      FROM Playlists
      WHERE hidden = 0
    ''')

    for pid, name in playlists:
        export_playlist(settings, db, pid, name, file_db)

    new_files=set(file_db.values())
    logger.info("cleaning up old files")
    for f in old_files:
        if f not in new_files:
            logger.debug("removing old file: %s", f)
            os.remove(f)

if __name__ == '__main__':
    main()
