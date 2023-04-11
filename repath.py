#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>
#

# repath.py
# ---------

import sys
import os
import shutil
import logging
import sqlite3
logger = logging.getLogger(__name__)

TRANSFORMS = [
    # Old symlinks
    (
        '/home/raskolnikov/media/mpd/music/alexandria',
        '/media/raskolnikov/alexandria/musica',
    ),
    (
        '/home/raskolnikov/media/mpd/music/hd-alexandria',
        '/media/raskolnikov/alexandria/musica',
    ),
    (
        '/var/lib/mpd/music/hd-raskolnikov',
        '/media/raskolnikov/alexandria/musica',
    ),
    # Moving stuff to new locations...
    (
        '/media/raskolnikov/alexandria/musica',
        '/run/media/raskolnikov/aleph/musica',
    ),
    (
        '/run/media/raskolnikov/alexandria/musica',
        '/run/media/raskolnikov/aleph/musica',
    ),
    (
        '/home/raskolnikov/sync/music/unsorted',
        '/run/media/raskolnikov/aleph/musica/unsorted/2017',
    ),
    (
        '/home/raskolnikov/sync/music/unsorted',
        '/run/media/raskolnikov/aleph/musica/unsorted/2018',
    ),
    (
        '/home/raskolnikov/sync/music/unsorted',
        '/run/media/raskolnikov/aleph/musica/unsorted/2019',
    ),
    (
        '/home/raskolnikov/sync/music/unsorted',
        '/run/media/raskolnikov/aleph/musica/unsorted/2020',
    ),
    (
        '/home/raskolnikov/sync/music/unsorted',
        '/run/media/raskolnikov/aleph/musica/unsorted/2021',
    ),
]

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')
    db = sqlite3.connect('mixxxdb.fixed.sqlite')

    for old_prefix, new_prefix in TRANSFORMS:
        logger.info("moving %s to %s" % (old_prefix, new_prefix))
        logger.info("finding matching locations")

        matches = db.execute('''
          SELECT id, location FROM track_locations WHERE location LIKE ?
        ''', (old_prefix + '%',))

        logger.info("fixing matching locations")
        for id, location in matches:
            new_location = new_prefix + location[len(old_prefix):]
            new_id = db.execute('''
                SELECT id FROM track_locations WHERE location = ?
            ''', (new_location,)).fetchone()
            if new_id:
                new_id, = new_id
                logger.info("moving from %s to %s", location, new_location)
                db.execute('''
                  UPDATE library SET location=? WHERE location=?
                ''', (new_id, id))
                db.execute('''
                  DELETE FROM track_analysis WHERE track_id=?
                ''', (id,))
                db.execute('''
                  DELETE FROM track_locations WHERE id=?
                ''', (id,))
            else:
                logger.info("no replacement for: %s", location)

    logger.info("commiting")
    db.commit()

if __name__ == '__main__':
    main()
