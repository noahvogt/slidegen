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

from wand.image import Image
from wand.color import Color
from wand.font import Font

import config as const

from .start_slide import StartSlide


class ClassicStartSlide(StartSlide):
    def get_slide(
        self,
        template_img: Image,
        book: str,
        text_author: str,
        melody_author: str,
    ) -> Image:
        start_img = template_img.clone()
        start_img.composite(
            self.get_attributions(text_author, melody_author),
            left=const.METADATA_X,
            top=const.ATTRIBUTIONS_Y,
        )
        start_img.composite(
            self.get_book(book), left=const.METADATA_X, top=const.BOOK_Y
        )
        return start_img.clone()

    def get_metadata(self, text: str) -> Image:
        with Image(
            width=const.WIDTH,
            height=const.HEIGHT,
            background=Color(const.BG_COLOR),
        ) as img:
            img.caption(
                text,
                font=Font(
                    const.FONT_PATH,
                    size=const.METADATA_FONT_SIZE,
                    color=Color(const.TEXT_COLOR),
                ),
            )
            img.trim()
            return img.clone()

    def get_attributions(self, text_author: str, melody_author: str) -> Image:
        if text_author == melody_author:
            return self.get_metadata("Text & Melodie: " + text_author)
        return self.get_metadata(
            "Text: " + text_author + "\nMelodie: " + melody_author
        )

    def get_book(self, book: str) -> Image:
        return self.get_metadata(book)
