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

import unittest

from song_files import SongFile
from song_plan import build_plan, choose_file, service_warnings


def song(name, title, key, structure, errors=()):
    return SongFile(
        name=name,
        header={"title": title, "structure": structure},
        structure=structure.split(","),
        errors=list(errors),
        key=key,
    )


SONGS = [
    song("Grosser Gott.txt", "Grosser Gott, wir loben dich", "gm 37", "1,2,3,4,5,6,7"),
    song("Immer wieder.txt", "Immer wieder koennt ich singen", "gm 268", "R,1,R,2,R,3,R"),
    song("Elohim de.txt", "Elohim (deutsch)", "Smu 136", "1,R,2,R"),
    song("Elohim ch.txt", "Elohim (schwitzerduetsch)", "Smu 136", "1,R,2,R"),
    song("Falsche Nummer.txt", "Ein ganz anderes Lied", "gm 500", "1,2"),
    song("Ohne Nummer.txt", "Herr du gibst uns Hoffnung", None, "1,2,3"),
]


def entry(nr, titel, lied_nr, strophen="", **extra):
    return {"stelle": f"Lied {lied_nr}", "lied_nr": lied_nr, "nr": nr,
            "titel": titel, "strophen": strophen, "auch": [],
            "offen": False, "alternative": False, "hinweis": None, **extra}


def plan(*entries):
    return build_plan({"lieder": list(entries)}, SONGS, 9)


class BuildPlanTest(unittest.TestCase):
    def test_folder_is_the_number_of_the_song_place(self):
        items = plan(entry("gm 37", "Großer Gott, wir loben dich", 1, "1-3"),
                     entry("gm 268", "Immer wieder könnt ich singen", 2, "2"))
        self.assertEqual([(i.folder, i.order) for i in items],
                         [(1, "1,2,3"), (2, "R,2,R")])
        self.assertEqual([i.warnings for i in items], [[], []])

    def test_alternative_gets_no_slides_only_a_note(self):
        items = plan(entry("gm 37", "Großer Gott, wir loben dich", 1),
                     entry("gm 268", "Immer wieder könnt ich singen", 1, alternative=True),
                     entry("gm 37", "Großer Gott, wir loben dich", 2))
        self.assertEqual([i.folder for i in items], [1, 2])
        self.assertEqual(items[0].warnings,
                         ["Alternative: gm 268 Immer wieder könnt ich singen (keine Folien)"])

    def test_further_song_of_a_place_goes_to_the_next_free_folder(self):
        items = plan(entry("gm 37", "Großer Gott, wir loben dich", 1),
                     entry("gm 268", "Immer wieder könnt ich singen", 1),
                     entry("gm 37", "Großer Gott, wir loben dich", 2))
        self.assertEqual([i.folder for i in items], [1, 2, 3])

    def test_open_place_and_song_without_slides(self):
        items = plan({"stelle": "Lied 1", "lied_nr": 1, "offen": True},
                     entry("gm 999", "Gibt es nicht", 2))
        self.assertIn("noch offen", items[0].warnings[0])
        self.assertEqual(items[1].order, "")
        self.assertIn("Keine Folien", items[1].warnings[0])

    def test_several_files_and_choosing_one(self):
        item = plan(entry("Smu 136", "Elohim, Gott isch der Schöpfer", 1))[0]
        self.assertEqual(len(item.files), 2)
        self.assertTrue(any("2 Dateien" in w for w in item.warnings))
        choose_file(item, "Elohim ch.txt", {s.name: s for s in SONGS})
        self.assertEqual(item.files[0], "Elohim ch.txt")

    def test_title_check_and_bad_verses(self):
        item = plan(entry("gm 500", "O Haupt voll Blut und Wunden", 1))[0]
        self.assertTrue(any(w.startswith("Titel weicht ab") for w in item.warnings))
        item = plan(entry("gm 37", "Großer Gott, wir loben dich", 1, "1-9"))[0]
        self.assertEqual(item.order, "1,2,3,4,5,6,7")
        self.assertTrue(any(w.startswith("Strophen «1-9»") for w in item.warnings))

    def test_song_without_number_found_by_its_title(self):
        item = plan(entry(None, "Herr, du gibst uns Hoffnung", 1))[0]
        self.assertEqual(item.files, ["Ohne Nummer.txt"])

    def test_too_many_songs(self):
        entries = [entry("gm 37", "Großer Gott, wir loben dich", n) for n in range(1, 10)]
        entries.append(entry("gm 268", "Immer wieder könnt ich singen", 9))
        self.assertIsNone(plan(*entries)[-1].folder)


class ServiceWarningsTest(unittest.TestCase):
    def test_states(self):
        self.assertTrue(service_warnings({"ablauf": {"vorhanden": False}}))
        self.assertTrue(service_warnings({"ablauf": {"vorhanden": True, "versandt": None}}))
        self.assertTrue(service_warnings({"ablauf": {"vorhanden": True, "geaendert": "2026-11-07 18:00:00", "versandt": "2026-11-07 17:00:00"}}))
        self.assertEqual(service_warnings({"ablauf": {"vorhanden": True, "geaendert": "2026-11-07 17:00:00", "versandt": "2026-11-07 17:00:10"}}), [])


if __name__ == "__main__":
    unittest.main()
