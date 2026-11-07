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

from song_structure import resolve_prompt, calculate_dashed_prompt_part

TWELVE = "1,2,3,4,5,6,7,8,9,10,11,12"


class ResolvePromptTest(unittest.TestCase):
    def check(self, structure, prompt, expected):
        valid, result = resolve_prompt(prompt, structure)
        if expected is None:
            self.assertFalse(valid, f"{structure} {prompt} -> {result}")
        else:
            self.assertTrue(valid, f"{structure} {prompt} invalid")
            self.assertEqual(result, expected, f"{structure} {prompt}")

    def test_refrains_added_for_single_verses_and_lists(self):
        self.check("1,R,2,R,3,R", "1,3", "1,R,3,R")
        self.check("1,R,2,R,3,R", "2", "2,R")
        self.check("1,R,2,R,3,R", "1-2,3", "1,R,2,R,3,R")
        self.check("R,1,R,2,R,3,R", "1,3", "R,1,R,3,R")
        self.check("R,1,R,2,R,3,R", "3", "R,3,R")
        self.check("1,2,R,3,4,R", "1,2", "1,2,R")
        self.check("1,2,3,4", "1,3", "1,3")

    def test_ranges_as_before(self):
        self.check("1,R,2,R,3,R", "1-3", "1,R,2,R,3,R")
        self.check("1,R,2,R,3,R", "2-3", "2,R,3,R")
        self.check("R,1,R,2,R,3,R", "2-3", "R,2,R,3,R")
        self.check("1,2,R,3,4,R", "3-4", "3,4,R")
        self.check("1,R,R,2,R", "1-2", "1,R,R,2,R")
        self.check("1,2,3,4", "1-3", "1,2,3")

    def test_refrain_after_verse_even_if_song_does_not_end_with_it(self):
        # before: "1-2" gave "1,R,2" because the song does not end with R
        self.check("1,R,2,R,3,R,4", "1-2", "1,R,2,R")

    def test_written_with_r_or_own_order_taken_as_is(self):
        self.check("1,R,2,R,3,R", "1,R,3,R", "1,R,3,R")
        self.check("1,R,2,R,3,R", "1-2,3,R,R", "1,R,2,R,3,R,R")
        self.check("1,R,2,R,3,R", "3,1", "3,1")
        self.check("1,2,3,4", "1,1,4,2,3", "1,1,4,2,3")

    def test_verses_from_ten_on(self):
        self.check(TWELVE, "9-10", "9,10")
        self.check(TWELVE, "10", "10")
        self.check(TWELVE, "2,11-12", "2,11,12")
        self.check(TWELVE, "1-12", TWELVE)

    def test_typing_variants(self):
        self.check("1,R,2,R,3,R", "1 – 3", "1,R,2,R,3,R")
        self.check("1,2,3,4", "1, 3", "1,3")

    def test_invalid(self):
        self.check("1,2,3,4", "5", None)
        self.check("1,2,3,4", "3-2", None)
        self.check("1,2,3,4", "1-123x", None)
        self.check("1,2,3,4", "R", None)
        self.check(TWELVE, "13", None)
        self.check("1,2,3,4", "", None)

    def test_structure_as_list(self):
        self.assertEqual(
            calculate_dashed_prompt_part(["1", "R", "2", "R", "3", "R"], "1", "2"),
            ["1", "R", "2", "R"],
        )


if __name__ == "__main__":
    unittest.main()
