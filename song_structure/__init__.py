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

"""
Which slides of a song to show: a verse prompt like "1-3", "1,3" or "1,R,2"
against the structure of the song file like "1,R,2,R,3,R".

- Verses without "R", in ascending order ("1,3", "2-4", "1-2,4"): the
  refrains come from the structure of the song (resolve_prompt()). This is
  what the Gottesdienstleitung writes in the Ablauf.
- With "R" or in an own order ("1,R,R", "3,1"): taken as written, ranges
  filled in from the structure (the behaviour before).

Only the standard library, so it can be tested without PyQt5 or Wand.
"""

from re import match

PROMPT_REGEX = r"^(([0-9]+|R)|[0-9]+-[0-9]+)(,(([0-9]+|R)|[0-9]+-[0-9]+))*$"


def structure_list(structure: str | list) -> list[str]:
    if isinstance(structure, str):
        return structure.replace(" ", "").split(",")
    return [element for element in structure if element != ","]


def normalize_prompt(prompt: str) -> str:
    """Spaces and the long dashes people type ("1–3") are fine."""
    return prompt.replace(" ", "").replace("–", "-").replace("—", "-")


def resolve_prompt(prompt: str, structure: str | list) -> tuple[bool, str]:
    """(valid, slide order as "1,R,2,R"). Invalid: unknown verses, bad
    syntax, ranges like "3-2"."""
    prompt = normalize_prompt(prompt)
    if not match(PROMPT_REGEX, prompt):
        return False, ""
    structure = structure_list(structure)
    allowed = set(structure)
    literal: list[str] = []
    verses: list[str] = []
    for element in prompt.split(","):
        if "-" in element:
            start_verse, end_verse = element.split("-")
            if int(start_verse) >= int(end_verse):
                return False, ""
            if start_verse not in allowed or end_verse not in allowed:
                return False, ""
            part = calculate_dashed_prompt_part(structure, start_verse, end_verse)
            literal += part
            verses += [verse for verse in part if verse != "R"]
        else:
            if element not in allowed:
                return False, ""
            literal.append(element)
            if element != "R":
                verses.append(element)

    numbers = [int(verse) for verse in verses]
    ascending = all(a < b for a, b in zip(numbers, numbers[1:]))
    if "R" in prompt.split(",") or not ascending:
        return True, ",".join(literal)
    return True, ",".join(add_refrains(verses, structure))


def add_refrains(verses: list[str], structure: list[str]) -> list[str]:
    """The chosen verses in the order of the structure, with their refrains:
    a refrain belongs to the verse before it; in a song that starts with the
    refrain also to the verse after it. Skipping verses never puts the
    refrain twice in a row, unless the song itself repeats it."""
    chosen = set(verses)
    starts_with_refrain = structure[0] == "R"
    kept = [False] * len(structure)
    out: list[str] = []
    for i, element in enumerate(structure):
        previous = structure[i - 1] if i > 0 else None
        if element != "R":
            kept[i] = element in chosen
        else:
            after_chosen = previous in chosen or (previous == "R" and kept[i - 1])
            before_chosen = (
                starts_with_refrain
                and i + 1 < len(structure)
                and structure[i + 1] in chosen
            )
            kept[i] = after_chosen or before_chosen
        if not kept[i]:
            continue
        repeated_in_song = previous == "R" and kept[i - 1]
        if element == "R" and out and out[-1] == "R" and not repeated_in_song:
            continue
        out.append(element)
    return out


def calculate_dashed_prompt_part(
    content: list, start_verse: str, end_verse: str
) -> list:
    """The part of the structure from start_verse to end_verse. A song that
    starts (ends) with the refrain keeps the refrain before (after) it."""
    content = structure_list(content)
    start_index = content.index(start_verse)
    if start_index != 0:
        if content[0] == "R" and content[start_index - 1] == "R":
            start_index -= 1
    end_index = content.index(end_verse)
    if end_index != len(content) - 1:
        if content[-1] == "R" and content[end_index + 1] == "R":
            end_index += 1

    return content[start_index : end_index + 1]
