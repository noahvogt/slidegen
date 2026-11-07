#!/usr/bin/env python3

# Copyright © 2026 Noah Vogt <noah@noahvogt.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Which songs have slides: JSON on stdout for the intern area of the website
(nightly job on the NAS, website/deploy/folien-sync.sh), keyed by song
number as in the Liederdatenbank:

    {"erzeugt": "...", "anzahl_dateien": 657,
     "lieder": {"gm 37": {"dateien": ["Grosser Gott, wir loben dich.txt"],
                          "strophen": [1, 2, 3, 4, 5, 6, 7],
                          "refrain": false}, ...},
     "fehler": ["Datei: Grund", ...]}

Files slidegen stops on are left out (listed under "fehler"), so the website
does not promise slides that cannot be made. Only the standard library.

    ./export_song_index.py ~/Documents/ssync-data > folien.json
"""

import json
import sys
from datetime import datetime, timezone

from song_files import read_songs


def song_index_json(directory: str) -> dict:
    songs = read_songs(directory)
    entries: dict[str, dict] = {}
    errors = []
    for song in songs:
        if song.errors:
            errors += [f"{song.name}: {error}" for error in song.errors]
            continue
        if not song.key:
            continue
        entry = entries.setdefault(
            song.key, {"dateien": [], "strophen": [], "refrain": False}
        )
        entry["dateien"].append(song.name)
        verses = {int(e) for e in song.structure if e != "R"}
        # several files (translations): the verses any of them has
        entry["strophen"] = sorted(set(entry["strophen"]) | verses)
        entry["refrain"] = entry["refrain"] or "R" in song.structure
    return {
        "erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "anzahl_dateien": len(songs),
        "lieder": dict(sorted(entries.items())),
        "fehler": errors,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: export_song_index.py DIR")
    json.dump(song_index_json(sys.argv[1]), sys.stdout, ensure_ascii=False)
