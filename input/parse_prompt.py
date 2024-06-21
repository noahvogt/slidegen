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
    prompt: str, full_structure: list
) -> tuple[bool, str]:
    if not match(
        r"^(([0-9]+|R)|[0-9]+-[0-9]+)(,(([0-9]+|R)|[0-9]+-[0-9]+))*$", prompt
    ):
        return False, ""

    allowed_elements = get_unique_structure_elements(full_structure)
    test_elements = prompt.split(",")
    for index, element in enumerate(test_elements):
        if "-" in element:
            splitted_dashpart = element.split("-")
            if splitted_dashpart[0] >= splitted_dashpart[1]:
                return False, ""
            if splitted_dashpart[0] not in allowed_elements:
                return False, ""
            if splitted_dashpart[1] not in allowed_elements:
                return False, ""

            dotted_part = calculate_dashed_prompt_part(
                full_structure, splitted_dashpart[0], splitted_dashpart[1]
            )
            dotted_part.reverse()
            test_elements[index] = dotted_part[0]
            for left_over_dotted_part_element in dotted_part[1:]:
                test_elements.insert(index, left_over_dotted_part_element)
        else:
            if element not in allowed_elements:
                return False, ""

    return True, ",".join(test_elements)


def calculate_dashed_prompt_part(
    content: list, start_verse: str, end_verse: str
) -> list:
    content = list(content)
    for i in content:
        if i == ",":
            content.remove(i)
    start_index = content.index(start_verse)
    if start_index != 0:
        if content[0] == "R" and content[start_index - 1] == "R":
            start_index -= 1
    end_index = content.index(end_verse)
    if end_index != len(content) - 1:
        if content[-1] == "R" and content[end_index + 1] == "R":
            end_index += 1

    return content[start_index : end_index + 1]
