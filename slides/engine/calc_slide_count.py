# Copyright © 2024 Noah Vogt <noah@noahvogt.com>

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

import config as const


def count_number_of_slides_to_be_generated(slidegen) -> int:
    slide_count: int = 0
    for structure in slidegen.chosen_structure:
        line_count: int = len(slidegen.songtext[structure].splitlines())
        if line_count > const.STRUCTURE_ELEMENT_MAX_LINES:
            slide_count += line_count // const.STRUCTURE_ELEMENT_MAX_LINES + 1
        else:
            slide_count += 1

    return slide_count
