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

import colorama

from wand.image import Image

from slides import (
    ClassicSongTemplate,
    ClassicStartSlide,
    ClassicSongSlide,
    generate_start_slide,
    generate_song_slides,
    generate_song_template,
    count_number_of_slides_to_be_generated,
)

from input import parse_prompt_input, parse_metadata, parse_songtext, parse_argv


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
        parse_argv(self)

    def execute(self) -> None:
        self.parse_file()
        self.calculate_desired_structures()
        self.generate_slides()

    def parse_file(self):
        parse_metadata(self)
        parse_songtext(self)

    def calculate_desired_structures(self) -> None:
        self.chosen_structure = parse_prompt_input(self)

    def generate_slides(self) -> None:
        template_img: Image = generate_song_template(self)

        slide_count: int = count_number_of_slides_to_be_generated(self)
        zfill_length: int = len(str(slide_count))

        generate_start_slide(self, template_img, zfill_length)
        generate_song_slides(self, slide_count, template_img, zfill_length)


def main() -> None:
    colorama.init()

    slidegen: Slidegen = Slidegen(
        ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide
    )
    slidegen.execute()


if __name__ == "__main__":
    main()
