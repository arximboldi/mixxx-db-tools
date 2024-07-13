#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>
#

# reimport.py
# -----------
#
# Reimports a playlist exported from Rekordbox. It assumes the tracks
# have been previously exported with export.py, so they can be found
# using the ID that is contained at the end of the filename.

import logging
import sqlite3
import os.path
import re
import sys
import shutil
import pathlib
import unicodedata
import m3u8

from pathlib import Path


logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    if len(sys.argv) != 2:
        logger.warning("need to pass a backup file")
        return

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')
    db = sqlite3.connect('mixxxdb.fixed.sqlite')


    playlist_file = sys.argv[1]
    playlist = m3u8.load(playlist_file)
    playlist_name = Path(playlist_file).stem

    playlist_id, = db.execute('''
      INSERT INTO Playlists (name, position, date_created, date_modified)
      VALUES (?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
      RETURNING id
    ''', (playlist_name,)).fetchone()

    logger.info("creating new playlist: %s, with id: %s", playlist_name, playlist_id)

    id_regex = re.compile('.*__(\d*)')
    position = 0
    for item in playlist.segments:
        position += 1
        path = Path(item.uri)
        matches = id_regex.match(path.stem)
        if matches == None:
            logger.warn("could not parse item: %s", path.name)
            continue
        track_id = matches[1]
        data = db.execute('''
          SELECT artist, title
          FROM library
          WHERE id=?
        ''', (track_id,)).fetchone()
        if data == None:
            logger.warn("could not finde item: %s", path.name)
            continue
        logger.info("found '%s' - '%s' for: %s", data[0], data[1], path.name)
        db.execute('''
          INSERT INTO PlaylistTracks (playlist_id, track_id, position, pl_datetime_added)
          VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (playlist_id, track_id, position))

    logger.info("committing")
    db.commit()

if __name__ == '__main__':
    main()
