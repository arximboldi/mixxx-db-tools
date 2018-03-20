#!/usr/bin/env python
#
# Copyright (C) 2018 Juan Pedro Bolivar Puente
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the MIT License, as detailed in the LICENSE
# file located at the root of this source code distribution,
# or here: <https://github.com/arximboldi/lager/blob/master/LICENSE>
#

# dedup.py
# --------
#
# This is a little tool for fixing Mixxx data-bases that has been
# corrupted due to the abuse of symlinks.
#
# This problem can occur when a folder that is in the data-base
# contain symlinks to another folder.  When later that other folder is
# added to the library directly, Mixxx sometimes thinks the newly
# found files are genuinely new, creating two entries in the
# data-base for the same path.

import sqlite3
import shutil
import os
import logging
import sys
import math

from tqdm import tqdm

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    logger.info("copying database")
    shutil.copyfile('./mixxxdb.sqlite',
                    './mixxxdb.fixed.sqlite')

    db = sqlite3.connect('mixxxdb.fixed.sqlite')
    logger.info("finding duplicates")
    duplicates = db.execute('''
      SELECT location, COUNT(*) c
      FROM library
      GROUP BY location
      HAVING c > 1
    ''')

    logger.info("fixing duplicates")
    for location, c in tqdm(duplicates):
        # find the duplicates
        res = list(db.execute('''
          SELECT id, cuepoint, bpm, timesplayed, rating
          FROM library
          WHERE location=?
        ''', (location,)))
        get_id          = lambda x: x[0]
        get_cuepoint    = lambda x: x[1]
        get_bpm         = lambda x: x[2]
        get_timesplayed = lambda x: x[3]
        get_rating      = lambda x: x[4]
        get_bpm_error   = lambda x: abs(get_bpm(x) * 2 -
                                        round(get_bpm(x) * 2)) \
                                    if get_bpm(x) else 2

        # remove the duplicates
        best_id = get_id(max(res, key=get_timesplayed))
        for item in res:
            id = get_id(item)
            if id == best_id: continue
            db.execute('''
              UPDATE cues SET track_id=? WHERE track_id=?
            ''', (best_id, id))
            db.execute('''
              UPDATE PlaylistTracks SET track_id=? WHERE track_id=?
            ''', (best_id, id))
            db.execute('''
              UPDATE crate_tracks SET track_id=? WHERE track_id=?
            ''', (best_id, id))
            db.execute('''
              DELETE FROM library WHERE id=?
            ''', (id,))
        # merge the duplicates into the best candidate
        db.execute('''
          UPDATE library
          SET cuepoint=?, bpm=?, timesplayed=?, rating=?
          WHERE id=?
        ''', (
            get_cuepoint(max(res, key=get_cuepoint)),
            get_bpm(min(res, key=get_bpm_error)),
            sum(map(get_timesplayed, res)),
            get_rating(max(res, key=get_rating)),
            best_id
        ))

    logger.info("committing")
    db.commit()

if __name__ == '__main__':
    main()
