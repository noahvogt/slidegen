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

"""Run from the repo root: python -m unittest discover tests"""

import tempfile
import unittest
from os import path

from song_files import book_key, canonical_book, read_song


class BookKeyTest(unittest.TestCase):
    def test_known_books(self):
        for book, key in (
            ("Gesangbuch «Gesangbuch der Mennoniten» Nr. 37", "gm 37"),
            ("Liederordner Nr. 18", "LO 18"),
            ("Gesangbuch «Liederordner» Nr.5", "LO 5"),
            ("Gesangbuch «Singt mit uns» Nr.230", "Smu 230"),
            ("Gesangbuch «Neues Gemeinschafts-Liederbuch» Nr. 1", "Nglb 1"),
            ("Gesangbuch «Neues Gemeinschaftsliederbuch» Nr. 442", "Nglb 442"),
        ):
            self.assertEqual(book_key(book), (key, ""), book)

    def test_unknown(self):
        self.assertIsNone(book_key("Unbekannt")[0])
        self.assertIsNone(book_key("Gemeinschaftsliederbuch Nr. 12")[0])
        self.assertIsNone(book_key("Songs Junger Christen 4")[0])

    def test_canonical_round_trip(self):
        for key in ("gm 37", "LO 18", "Smu 230", "Nglb 442"):
            self.assertEqual(book_key(canonical_book(key))[0], key)


class ReadSongTest(unittest.TestCase):
    def song(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = path.join(d, "Lied.txt")
            with open(p, "w", encoding="utf-8") as w:
                w.write(text)
            return read_song(p)

    HEADER = "title: T\nbook: Liederordner Nr. 18\ntext: a\nmelody: b\n"

    def test_valid(self):
        s = self.song(self.HEADER + "structure: 1,R,2,R\n\n[R]\nr\n\n[1]\na\n\n[2]\nb\n")
        self.assertEqual(s.errors, [])
        self.assertEqual(s.key, "LO 18")

    def test_errors(self):
        s = self.song(self.HEADER + "structure: 1,R,2 \n\n[1]\na\n")
        self.assertTrue(any("Kopfzeile 5" in e for e in s.errors), s.errors)
        s = self.song(self.HEADER + "structure: 1,2\n\n[1] Text\na\n\n[2]\nb\n")
        self.assertTrue(any("Text hinter" in e for e in s.errors), s.errors)
        self.assertTrue(any("[1] fehlt" in e for e in s.errors), s.errors)
        s = self.song(self.HEADER + "structure: 1\n\n[1]\n" + "x" * 85 + "\n")
        self.assertTrue(any("länger" in e for e in s.errors), s.errors)

    def test_note_refrain_missing_at_end(self):
        s = self.song(self.HEADER + "structure: R,1,R,2\n\n[R]\nr\n\n[1]\na\n\n[2]\nb\n")
        self.assertTrue(any("endet ohne R" in n for n in s.notes), s.notes)


if __name__ == "__main__":
    unittest.main()
