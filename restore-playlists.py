#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>

# restore-playlists.py
# --------------------
#
# Copies enties that are renferenced in playlists but somehow do not
# appear in the library.
#
# This has happened because of the dedupe.py script not working
# properly before, as it wasn't giving priority to versions with
# playlists... even though theoretically it was updting the playlists
# as well!

import os.path
import re
import sys
import shutil
import pathlib
import logging
import sqlite3

logger = logging.getLogger(__name__)

def restore_file(db, tid):
    row = db.execute('''
      SELECT *
      FROM library
      WHERE id=?
    ''', (tid,)).fetchone()
    if row != None:
        return # track is there

    logger.info("restoring: %s", tid)

    row = db.execute('''
      SELECT *
      FROM backup.library
      WHERE id=?
    ''', (tid,)).fetchone()

    # copy and fetch from library, assume new version has at least all
    # the attrs that the old version has
    db.execute('''
      INSERT INTO library(''' + ", ".join(row.keys()) + ''')
      SELECT ''' + ", ".join(row.keys()) + ''' FROM backup.library
      WHERE id=?
    ''', (tid,))
    location, artist, title, bpm = db.execute('''
      SELECT location, artist, title, bpm
      FROM library
      WHERE id=?
    ''', (tid,)).fetchone()

    # copy and fetch location
    db.execute('''
      INSERT INTO track_locations
      SELECT * FROM backup.track_locations
      WHERE id=?
    ''', (location,))
    path_str, = db.execute('''
      SELECT location
      FROM track_locations
      WHERE id=?
    ''', (location,)).fetchone()

    # copy a bunch of other things
    db.execute('''
      REPLACE INTO track_analysis
      SELECT * FROM backup.track_analysis
      WHERE track_id=?
    ''', (tid,))
    db.execute('''
      REPLACE INTO cues
      SELECT * FROM backup.cues
      WHERE track_id=?
    ''', (tid,))

    logger.info("restored: %s", path_str)


def restore_playlist(db, pid, name):
    tracks = db.execute('''
      SELECT track_id, position
      FROM PlaylistTracks
      WHERE playlist_id=?
      ORDER BY position
    ''', (pid,))
    logger.info("relocating playlist: %s", name)

    for tid, tpos in tracks:
        restore_file(db, tid)

def main():
    if len(sys.argv) != 2:
        logger.warning("need to pass a backup file")
        return

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')

    db = sqlite3.connect('mixxxdb.fixed.sqlite')
    db.row_factory = sqlite3.Row

    db.execute('''
      ATTACH DATABASE ? AS backup
    ''', (sys.argv[1],))

    playlists = db.execute('''
      SELECT id, name
      FROM Playlists
      WHERE hidden = 0
    ''')

    for pid, name in playlists:
        restore_playlist(db, pid, name)

    logger.info("committing")
    db.commit()

if __name__ == '__main__':
    main()
