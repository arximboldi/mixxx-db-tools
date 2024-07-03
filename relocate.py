#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>
#

# relocate.py
# -----------
#
# Goes through every file that is referenced in playlists and that is
# missing, and tries to find other entries that are similar and could
# replace it, using heuristics (artist name, track name, etc.), not
# necessarily the same file...

import os.path
import re
import sys
import shutil
import pathlib
import logging
import sqlite3

logger = logging.getLogger(__name__)

def relocate_file(db, tid):
    # otherwise copy the file and return the resulting filename
    location, artist, title, bpm = db.execute('''
      SELECT location, artist, title, bpm
      FROM library
      WHERE id=?
    ''', (tid,)).fetchone()
    all_attrs = db.execute('''
      SELECT *
      FROM library
      WHERE id=?
    ''', (tid,)).fetchone()
    path_str, = db.execute('''
      SELECT location
      FROM track_locations
      WHERE id=?
    ''', (location,)).fetchone()

    src_file=pathlib.Path(path_str)
    if src_file.exists():
        return

    logger.info("relocating file: %s", path_str)
    matches = db.execute('''
      SELECT *
      FROM library
      WHERE id<>? AND artist LIKE ? AND title LIKE ?
    ''', (tid, artist, title))
    best_match = None
    best_match_rank = 0
    for match in matches:
        logger.debug("considering: %s", match)
        rank = [a == b for a, b in zip(match, all_attrs)].count(True)
        if rank > best_match_rank:
            best_match_rank = rank
            best_match = match

    new_location, = db.execute('''
      SELECT location
      FROM library
      WHERE id=?
    ''', (match[0],)).fetchone()
    new_path_str, = db.execute('''
      SELECT location
      FROM track_locations
      WHERE id=?
    ''', (new_location,)).fetchone()

    logger.debug("best match: %s", match)
    logger.info("new path: %s", new_path_str)

    if not best_match:
        logger.warning("no alternative found for: %s", path_str)
    else:
        db.execute('''
          UPDATE library SET location=? WHERE id=?
        ''', (new_location, tid))

def relocate_playlist(db, pid, name):
    tracks = db.execute('''
      SELECT track_id, position
      FROM PlaylistTracks
      WHERE playlist_id=?
      ORDER BY position
    ''', (pid,))
    logger.info("relocating playlist: %s", name)

    for tid, tpos in tracks:
        relocate_file(db, tid)

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')
    db = sqlite3.connect('mixxxdb.fixed.sqlite')

    playlists = db.execute('''
      SELECT id, name
      FROM Playlists
      WHERE hidden = 0
    ''')

    for pid, name in playlists:
        relocate_playlist(db, pid, name)

    logger.info("committing")
    db.commit()

if __name__ == '__main__':
    main()
