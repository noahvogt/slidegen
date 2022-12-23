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

from os import path
import re
import sys

import colorama

from wand.exceptions import BlobError

from utils import (
    log,
    error_msg,
    get_songtext_by_structure,
    structure_as_list,
    get_unique_structure_elements,
)

from slides import ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide

try:
    import config.config as const  # pyright: ignore [reportMissingImports]
except ModuleNotFoundError:
    log("no costom config found, using defaults")
    import config.default_config as const


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

    def generate_slides(self) -> None:
        song_template = self.song_template_form()
        log("generating template...")
        template_img = song_template.get_template(self.metadata["title"])

        first_slide = self.start_slide_form()
        log("generating start slide...")
        start_slide_img = first_slide.get_slide(
            template_img,
            self.metadata["book"],
            self.metadata["text"],
            self.metadata["melody"],
        )
        start_slide_img.format = const.IMAGE_FORMAT
        try:
            start_slide_img.save(
                filename=path.join(
                    self.output_dir,
                    const.FILE_NAMEING + "1." + const.FILE_EXTENSION,
                )
            )
        except BlobError:
            error_msg("could not write start slide to target directory")

        log("generating song slides...")
        # unique_structures: list = list(set(self.chosen_structure))

        # count number of slides to be generated
        slide_count: int = 0
        for structure in self.chosen_structure:
            line_count: int = len(self.songtext[structure].splitlines())
            if line_count > const.STRUCTURE_ELEMENT_MAX_LINES:
                slide_count += (
                    line_count // const.STRUCTURE_ELEMENT_MAX_LINES + 1
                )
            else:
                slide_count += 1

        current_slide_index: int = 0

        for index, structure in enumerate(self.chosen_structure):
            structure_element_splitted: list = self.songtext[
                structure
            ].splitlines()
            line_count = len(structure_element_splitted)
            use_line_ranges_per_index = []
            use_lines_per_index = []
            if line_count <= const.STRUCTURE_ELEMENT_MAX_LINES:
                inner_slide_count = 1
            else:
                inner_slide_count: int = (
                    line_count // const.STRUCTURE_ELEMENT_MAX_LINES + 1
                )
                use_lines_per_index = [
                    line_count // inner_slide_count
                ] * inner_slide_count

                for inner_slide in range(inner_slide_count):
                    if sum(use_lines_per_index) == line_count:
                        break
                    use_lines_per_index[inner_slide] = (
                        use_lines_per_index[inner_slide] + 1
                    )
                for inner_slide in range(inner_slide_count):
                    use_line_ranges_per_index.append(
                        sum(use_lines_per_index[:inner_slide])
                    )

            for inner_slide in range(inner_slide_count):
                current_slide_index += 1

                log(
                    "generating song slide [{} / {}]...".format(
                        current_slide_index, slide_count
                    )
                )

                if inner_slide_count == 1:
                    structure_element_value: str = self.songtext[structure]
                else:
                    splitted_wanted_range: list = structure_element_splitted[
                        use_line_ranges_per_index[
                            inner_slide
                        ] : use_line_ranges_per_index[inner_slide]
                        + use_lines_per_index[inner_slide]
                    ]
                    structure_element_value: str = ""
                    for element in splitted_wanted_range:
                        structure_element_value += element + "\n"

                    structure_element_value = structure_element_value[:-1]

                song_slide = self.song_slide_form()
                song_slide_img = song_slide.get_slide(
                    template_img,
                    structure_element_value,
                    self.chosen_structure,
                    index,
                    bool(
                        inner_slide_count != 1
                        and inner_slide != inner_slide_count - 1
                    ),
                )
                song_slide_img.format = const.IMAGE_FORMAT
                try:
                    song_slide_img.save(
                        filename=path.join(
                            self.output_dir,
                            const.FILE_NAMEING
                            + str(current_slide_index + 1)
                            + "."
                            + const.FILE_EXTENSION,
                        )
                    )
                except BlobError:
                    error_msg("could not write slide to target directory")

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
                r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))+$",
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
        full_structure_str = str(self.metadata["structure"])
        full_structure_list = structure_as_list(full_structure_str)
        if len(self.chosen_structure) == 0:
            self.chosen_structure = structure_as_list(full_structure_str)
            log("chosen structure: {}".format(str(self.chosen_structure)))
            return
        if not "-" in self.chosen_structure:
            self.chosen_structure = structure_as_list(
                str(self.chosen_structure)
            )
            log("chosen structure: {}".format(str(self.chosen_structure)))
            return

        dash_index = str(self.chosen_structure).find("-")
        start_verse = str(self.chosen_structure[:dash_index]).strip()
        end_verse = str(self.chosen_structure[dash_index + 1 :]).strip()

        try:
            if int(start_verse) >= int(end_verse):
                error_msg("{} < {} must be true".format(start_verse, end_verse))
            if start_verse not in full_structure_str:
                error_msg("structure {} unknown".format(start_verse))
            if end_verse not in full_structure_str:
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

        self.chosen_structure = full_structure_list[start_index : end_index + 1]
        log("chosen structure: {}".format(str(self.chosen_structure)))

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
