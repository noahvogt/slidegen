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

from utils import (
    log,
    structure_as_list,
)
from song_structure import resolve_prompt


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
    """See song_structure: verses without "R" get their refrains from the
    structure, prompts with "R" or an own order are taken as written."""
    return resolve_prompt(prompt, full_structure)
