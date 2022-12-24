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

import config as const

from .log import error_msg


def get_songtext_by_structure(content: list, structure: str) -> str:
    found_desired_structure: bool = False
    output_str: str = ""

    for line in content:
        stripped_line: str = line.strip()
        line_length: int = len(line)
        if line_length > const.STRUCTURE_ELEMENT_PER_LINE_CHAR_LIMIT:
            if line[-1] == "\n":
                line = line[:-1]
            error_msg(
                "line is configured to a character limit of "
                + str(const.STRUCTURE_ELEMENT_PER_LINE_CHAR_LIMIT)
                + " but has {} characters: \n{}".format(line_length, line)
            )
        if found_desired_structure:
            if stripped_line.startswith("[") and stripped_line.endswith("]"):
                break
            output_str += stripped_line + "\n"

        if (
            stripped_line.startswith("[")
            and stripped_line.endswith("]")
            and structure in stripped_line
        ):
            found_desired_structure: bool = True

    return output_str[:-1]


def structure_as_list(structure: str) -> list:
    return structure.replace(" ", "").split(",")


def get_unique_structure_elements(structure: list) -> list:
    return list(dict.fromkeys(structure))
