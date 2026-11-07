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
Report on a folder of song files (slidegen format): files slidegen stops on,
files without a song number, numbers with several files, things to check.
Changes nothing. With --fix-book OUTDIR, the files whose "book:" line is
not in the canonical form are written there corrected (only that line).

    ./check_song_files.py ~/Documents/ssync-data
    ./check_song_files.py ~/Documents/ssync-data --fix-book /tmp/fixed
"""

import argparse
import sys
from os import makedirs, path

from song_files import book_key, canonical_book, read_songs, song_index

try:
    import config as const

    LINE_LIMIT = const.STRUCTURE_ELEMENT_PER_LINE_CHAR_LIMIT
except ImportError:
    LINE_LIMIT = 85


def section(title: str, rows: list[str]) -> None:
    print(f"\n## {title} ({len(rows)})")
    for row in rows or ["–"]:
        print(f"- {row}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("directory")
    parser.add_argument("--fix-book", metavar="OUTDIR")
    args = parser.parse_args()

    songs = read_songs(args.directory, LINE_LIMIT)
    index = song_index(songs)
    print(f"# Liedtexte in {args.directory}: {len(songs)} Dateien")

    section(
        "Fehler: slidegen bricht bei diesen Dateien ab",
        [f"{s.name}: {e}" for s in songs for e in s.errors],
    )
    no_key = []
    to_fix = []
    for song in songs:
        book = song.header.get("book")
        if book is None:
            continue
        key, reason = book_key(book)
        if key is None:
            no_key.append(f"{song.name}: {reason} («{book}»)")
        elif book != canonical_book(key):
            to_fix.append((song, key))
    section("Ohne Liednummer (Zuordnung zum Ablauf nicht möglich)", no_key)
    section(
        "book: nicht einheitlich (--fix-book korrigiert)",
        [
            f"{s.name}: «{s.header['book']}» → «{canonical_book(k)}»"
            for s, k in to_fix
        ],
    )
    section(
        "Mehrere Dateien mit derselben Nummer",
        [
            f"{key}: " + " | ".join(names)
            for key, names in sorted(index.items())
            if len(names) > 1
        ],
    )
    section(
        "Bitte prüfen",
        [f"{s.name}: {n}" for s in songs for n in s.notes],
    )

    if args.fix_book:
        makedirs(args.fix_book, exist_ok=True)
        for song, key in to_fix:
            source = path.join(args.directory, song.name)
            with open(source, encoding="utf-8-sig") as reader:
                lines = reader.read().split("\n")
            # only the header line, the first "book:"
            first = next(i for i, l in enumerate(lines) if l.startswith("book: "))
            lines[first] = "book: " + canonical_book(key)
            with open(
                path.join(args.fix_book, song.name), "w", encoding="utf-8"
            ) as writer:
                writer.write("\n".join(lines))
        print(f"\n{len(to_fix)} korrigierte Dateien in {args.fix_book}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
