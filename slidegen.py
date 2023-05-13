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
    SlideStyle,
    generate_slides,
    generate_song_template,
    count_number_of_slides_to_be_generated,
)

from input import (
    parse_prompt_input,
    parse_metadata,
    parse_songtext,
    parse_argv_as_tuple,
)


class Slidegen:
    def __init__(
        self,
        slide_style: SlideStyle,
        song_file_path: str,
        output_dir: str,
        chosen_structure: str | list,
    ) -> None:
        self.metadata: dict = {"": ""}
        self.songtext: dict = {"": ""}
        self.song_file_path: str = song_file_path
        self.song_file_content: list = []
        self.output_dir: str = output_dir
        self.chosen_structure = chosen_structure
        self.slide_style: SlideStyle = slide_style

    def execute(self, disable_async=False) -> None:
        self.parse_file()
        self.calculate_desired_structures()
        self.generate_slides(disable_async)

    def parse_file(self):
        parse_metadata(self)
        parse_songtext(self)

    def calculate_desired_structures(self) -> None:
        self.chosen_structure = parse_prompt_input(self)

    def generate_slides(self, disable_async: bool) -> None:
        template_img: Image = generate_song_template(self)

        slide_count: int = count_number_of_slides_to_be_generated(self)
        zfill_length: int = len(str(slide_count))

        generate_slides(
            self, slide_count, template_img, zfill_length, disable_async
        )


def main() -> None:
    colorama.init()

    classic_slide_style = SlideStyle(
        ClassicSongTemplate,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicStartSlide,  # pyright: ignore [reportGeneralTypeIssues]
        ClassicSongSlide,  # pyright: ignore [reportGeneralTypeIssues]
    )
    slidegen = Slidegen(classic_slide_style, *parse_argv_as_tuple())
    slidegen.execute()


if __name__ == "__main__":
    main()
