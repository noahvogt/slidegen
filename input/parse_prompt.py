"""
Copyright © 2022 Noah Vogt <noah@noahvogt.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from utils import (
    log,
    error_msg,
    structure_as_list,
)


def parse_prompt_input(slidegen) -> list:
    full_structure_list = structure_as_list(slidegen.metadata["structure"])
    if len(slidegen.chosen_structure) == 0:
        log("chosen structure: {}".format(str(slidegen.chosen_structure)))
        return structure_as_list(slidegen.metadata["structure"])
    if not "-" in slidegen.chosen_structure:
        log("chosen structure: {}".format(str(slidegen.chosen_structure)))
        return structure_as_list(str(slidegen.chosen_structure))

    dash_index = str(slidegen.chosen_structure).find("-")
    start_verse = str(slidegen.chosen_structure[:dash_index]).strip()
    end_verse = str(slidegen.chosen_structure[dash_index + 1 :]).strip()

    try:
        if int(start_verse) >= int(end_verse):
            error_msg("{} < {} must be true".format(start_verse, end_verse))
        if start_verse not in slidegen.metadata["structure"]:
            error_msg("structure {} unknown".format(start_verse))
        if end_verse not in slidegen.metadata["structure"]:
            error_msg("structure {} unknown".format(end_verse))
    except (ValueError, IndexError):
        error_msg("please choose a valid integer for the song structure")

    start_index = full_structure_list.index(start_verse)
    if start_index != 0:
        if (
            full_structure_list[0] == "R"
            and full_structure_list[start_index - 1] == "R"
        ):
            start_index -= 1
    end_index = full_structure_list.index(end_verse)
    if end_index != len(full_structure_list) - 1:
        if (
            full_structure_list[-1] == "R"
            and full_structure_list[end_index + 1] == "R"
        ):
            end_index += 1

    log("chosen structure: {}".format(str(slidegen.chosen_structure)))
    return full_structure_list[start_index : end_index + 1]
