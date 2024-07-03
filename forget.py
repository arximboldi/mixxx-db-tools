#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>

# forget.py
# ---------
#
# Remove files that are marked as deleted and are not referenced from
# any playslist.

import sys
import os
import shutil
import logging
import sqlite3
logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')
    db = sqlite3.connect('mixxxdb.fixed.sqlite')

    db.execute('''
      DELETE FROM track_locations
      WHERE fs_deleted=1
        AND id NOT IN (SELECT track_id FROM track_analysis)
        AND id NOT IN (SELECT location
                       FROM library
                       WHERE id IN (SELECT track_id FROM PlaylistTracks)
                          OR id IN (SELECT track_id FROM crate_tracks))
    ''')
    db.commit()

if __name__ == '__main__':
    main()
