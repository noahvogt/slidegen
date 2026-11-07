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

from export_song_index import song_index_json

HEADER = "title: {t}\nbook: {b}\ntext: a\nmelody: b\nstructure: {s}\n\n"


def write(directory, name, book, structure, sections):
    with open(path.join(directory, name), "w", encoding="utf-8") as w:
        w.write(HEADER.format(t=name, b=book, s=structure))
        for s in sections:
            w.write(f"[{s}]\ntext\n\n")


class ExportTest(unittest.TestCase):
    def test_export(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "A.txt", "Liederordner Nr. 18", "1,R,2,R", ["R", "1", "2"])
            write(d, "B de.txt", "Gesangbuch «Singt mit uns» Nr. 136", "1,2", ["1", "2"])
            write(d, "B ch.txt", "Gesangbuch «Singt mit uns» Nr. 136", "1,2,3", ["1", "2", "3"])
            write(d, "C.txt", "Unbekannt", "1", ["1"])
            write(d, "D.txt", "Liederordner Nr. 5", "1,2", ["1"])  # [2] missing
            data = song_index_json(d)
        self.assertEqual(data["anzahl_dateien"], 5)
        self.assertEqual(
            data["lieder"]["LO 18"],
            {"dateien": ["A.txt"], "strophen": [1, 2], "refrain": True},
        )
        self.assertEqual(data["lieder"]["Smu 136"]["strophen"], [1, 2, 3])
        self.assertEqual(len(data["lieder"]["Smu 136"]["dateien"]), 2)
        self.assertNotIn("LO 5", data["lieder"])
        self.assertTrue(any(e.startswith("D.txt") for e in data["fehler"]))


if __name__ == "__main__":
    unittest.main()
