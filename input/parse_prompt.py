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

from re import match

from utils import (
    log,
    structure_as_list,
    get_unique_structure_elements,
)


def parse_prompt_input(slidegen) -> list:
    calculated_prompt = generate_final_prompt(
        str(slidegen.chosen_structure), slidegen.metadata["structure"]
    )
    log(
        "chosen structure: {}".format(calculated_prompt),
        color="cyan",
    )
    return structure_as_list(calculated_prompt)


def generate_final_prompt(structure_prompt_answer, full_song_structure) -> str:
    valid_prompt, calculated_prompt = is_and_give_prompt_input_valid(
        structure_prompt_answer, full_song_structure
    )

    if not valid_prompt:
        log(
            "warning: prompt input '{}' is invalid, defaulting to full".format(
                structure_prompt_answer
            )
            + " song structure...",
            color="cyan",
        )
        calculated_prompt = full_song_structure
    return calculated_prompt


def is_and_give_prompt_input_valid(
    prompt: str, full_structure: str | list
) -> tuple[bool, str]:
    if not match(r"^(([0-9]+|R)|[0-9]+-[0-9]+)(,(([0-9]+|R)|[0-9]+-[0-9]+))*$", prompt):
        return False, ""

    # the structure comes as "1,2,R,3" from the song file: compare whole
    # elements, not characters, so that verses from 10 on work as well
    if isinstance(full_structure, str):
        full_structure = structure_as_list(full_structure)
    allowed_elements = get_unique_structure_elements(full_structure)
    result: list[str] = []
    for element in prompt.split(","):
        if "-" in element:
            start_verse, end_verse = element.split("-")
            if int(start_verse) >= int(end_verse):
                return False, ""
            if start_verse not in allowed_elements or end_verse not in allowed_elements:
                return False, ""
            result += calculate_dashed_prompt_part(
                full_structure, start_verse, end_verse
            )
        else:
            if element not in allowed_elements:
                return False, ""
            result.append(element)

    return True, ",".join(result)


def calculate_dashed_prompt_part(
    content: list, start_verse: str, end_verse: str
) -> list:
    """The part of the structure from start_verse to end_verse. A song that
    starts (ends) with the refrain keeps the refrain before (after) it."""
    content = [element for element in content if element != ","]
    start_index = content.index(start_verse)
    if start_index != 0:
        if content[0] == "R" and content[start_index - 1] == "R":
            start_index -= 1
    end_index = content.index(end_verse)
    if end_index != len(content) - 1:
        if content[-1] == "R" and content[end_index + 1] == "R":
            end_index += 1

    return content[start_index : end_index + 1]
