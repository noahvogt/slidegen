#!/usr/bin/env python3

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

import re
import sys

import colorama

from wand.image import Image

from utils import (
    log,
    error_msg,
    get_songtext_by_structure,
    structure_as_list,
    get_unique_structure_elements,
)

from slides import (
    ClassicSongTemplate,
    ClassicStartSlide,
    ClassicSongSlide,
    generate_start_slide,
    generate_song_slides,
    generate_song_template,
)

import config as const

from prompt import parse_input


class Slidegen:
    def __init__(
        self, song_template_form, start_slide_form, song_slide_form
    ) -> None:
        self.metadata: dict = {"": ""}
        self.songtext: dict = {"": ""}
        self.song_file_path: str = ""
        self.song_file_content: list = []
        self.output_dir: str = ""
        self.chosen_structure: list | str = ""
        self.generated_slides: list = []
        self.song_template_form = song_template_form
        self.start_slide_form = start_slide_form
        self.song_slide_form = song_slide_form
        self.parse_argv()

    def execute(self) -> None:
        self.parse_file()
        self.calculate_desired_structures()
        self.generate_slides()

    def count_number_of_slides_to_be_generated(self) -> int:
        slide_count: int = 0
        for structure in self.chosen_structure:
            line_count: int = len(self.songtext[structure].splitlines())
            if line_count > const.STRUCTURE_ELEMENT_MAX_LINES:
                slide_count += (
                    line_count // const.STRUCTURE_ELEMENT_MAX_LINES + 1
                )
            else:
                slide_count += 1

        return slide_count

    def generate_slides(self) -> None:
        template_img: Image = generate_song_template(self)

        slide_count: int = self.count_number_of_slides_to_be_generated()
        zfill_length: int = len(str(slide_count))

        generate_start_slide(self, template_img, zfill_length)
        generate_song_slides(self, slide_count, template_img, zfill_length)

    def parse_file(self) -> None:
        self.parse_metadata()
        self.parse_songtext()

    def parse_metadata(self) -> None:
        metadata_dict = dict.fromkeys(const.METADATA_STRINGS)
        try:
            with open(self.song_file_path, mode="r", encoding="utf8") as opener:
                content = opener.readlines()
        except IOError:
            error_msg(
                "could not read the the song input file: '{}'".format(
                    self.song_file_path
                )
            )
        valid_metadata_strings = list(const.METADATA_STRINGS)

        for line_nr, line in enumerate(content):
            if len(valid_metadata_strings) == 0:
                content = content[line_nr:]
                break
            if not re.match(
                r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))*$",
                line,
            ):
                if line[-1] == "\n":
                    line = line[:-1]
                missing_metadata_strs = ""
                for metadata_str in valid_metadata_strings:
                    missing_metadata_strs += ", " + metadata_str
                missing_metadata_strs = missing_metadata_strs[2:]
                error_msg(
                    "invalid metadata syntax on line {}:\n{}\nThe ".format(
                        line_nr + 1, line
                    )
                    + "following metadata strings are still missing: {}".format(
                        missing_metadata_strs
                    )
                )
            metadata_str = line[: line.index(":")]
            if metadata_str in valid_metadata_strings:
                metadata_dict[metadata_str] = line[line.index(": ") + 2 : -1]
                valid_metadata_strings.remove(metadata_str)
                continue

            error_msg("invalid metadata string '{}'".format(metadata_str))

        self.metadata = metadata_dict
        self.song_file_content = content

    def parse_songtext(self) -> None:
        unique_structures = get_unique_structure_elements(
            structure_as_list(self.metadata["structure"])
        )
        output_dict = dict.fromkeys(unique_structures)

        for structure in unique_structures:
            output_dict[structure] = get_songtext_by_structure(
                self.song_file_content, structure
            )

        self.songtext = output_dict

    def calculate_desired_structures(self) -> None:
        self.chosen_structure: list | str = parse_input(
            str(self.metadata["structure"]), self.chosen_structure
        )

    def parse_argv(self) -> None:
        try:
            self.song_file_path = sys.argv[1]
            self.output_dir = sys.argv[2]
        except IndexError:
            error_msg("incorrect amount of arguments provided, exiting...")
        try:
            self.chosen_structure = sys.argv[3]
            if self.chosen_structure.strip() == "":
                self.chosen_structure = ""
        except IndexError:
            self.chosen_structure = ""

        log("parsing {}...".format(self.song_file_path))


def main() -> None:
    colorama.init()

    slidegen: Slidegen = Slidegen(
        ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide
    )
    slidegen.execute()


if __name__ == "__main__":
    main()
