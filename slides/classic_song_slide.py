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

from wand.image import Image
from wand.drawing import Drawing
from wand.font import Font
from wand.color import Color

import config as const

from utils import get_empty_image
from .song_slide import SongSlide


class ClassicSongSlide(SongSlide):
    def get_slide(
        self,
        template_img: Image,
        slide_text: str,
        song_structure: list,
        index: int,
        use_arrow: bool,
    ) -> Image:
        canvas_img, font_size = self.get_text_canvas(slide_text)
        verse_or_chorus = song_structure[index]
        bg_img = template_img.clone()
        if "R" not in verse_or_chorus:
            bg_img.composite(
                self.get_index(verse_or_chorus, font_size),
                top=const.STRUCTURE_ELEMENT_Y,
                left=const.STRUCTURE_ELEMENT_X,
            )
        bg_img.composite(
            canvas_img, top=const.TEXT_CANVAS_Y, left=const.TEXT_CANVAS_X
        )
        if use_arrow:
            bg_img.composite(
                self.get_arrow(), top=const.ARROW_Y, left=const.ARROW_X
            )
        bg_img.composite(
            self.get_structure_info_display(song_structure, index),
            top=const.INFODISPLAY_Y,
            left=const.INFODISPLAY_X,
        )
        return bg_img.clone()

    def get_arrow(self) -> Image:
        with Drawing() as draw:
            draw.stroke_width = 1
            draw.stroke_color = Color(const.ARROW_COLOR)
            draw.fill_color = Color(const.ARROW_COLOR)
            arrow_width = const.ARROW_HEIGHT * 3 // 2

            draw.path_start()
            draw.path_move(
                to=(0, const.ARROW_HEIGHT / 2 - const.ARROW_HEIGHT / 10)
            )
            draw.path_line(
                to=(0, const.ARROW_HEIGHT / 2 + const.ARROW_HEIGHT / 10)
            )
            draw.path_line(
                to=(
                    arrow_width / 3 * 2,
                    const.ARROW_HEIGHT / 2 + const.ARROW_HEIGHT / 10,
                )
            )
            draw.path_line(to=(arrow_width / 3 * 2, const.ARROW_HEIGHT))
            draw.path_line(to=(arrow_width, const.ARROW_HEIGHT / 2))
            draw.path_line(to=(arrow_width / 3 * 2, 0))
            draw.path_line(
                to=(
                    arrow_width / 3 * 2,
                    const.ARROW_HEIGHT / 2 - const.ARROW_HEIGHT / 10,
                )
            )
            draw.path_close()
            draw.path_finish()

            with Image(
                width=arrow_width,
                height=const.ARROW_HEIGHT,
                background=Color(const.BG_COLOR),
            ) as image:
                draw(image)
                return image.clone()

    def get_text_canvas(self, slide_text: str) -> tuple[Image, int]:
        font_size = const.MAX_CANVAS_FONT_SIZE
        while font_size >= const.MIN_CANVAS_FONT_SIZE:
            with Drawing() as draw:
                draw.fill_color = Color(const.TEXT_COLOR)
                draw.text_interline_spacing = const.INTERLINE_SPACING
                draw.font_size = font_size
                draw.font = const.FONT
                draw.text(0, font_size, slide_text)
                with Image(
                    width=const.WIDTH,
                    height=const.HEIGHT,
                    background=Color(const.BG_COLOR),
                ) as img:
                    draw(img)
                    img.trim()
                    if (
                        img.width > const.TEXT_CANVAS_WIDTH
                        or img.height > const.TEXT_CANVAS_HEIGHT
                    ):
                        font_size -= const.CANVAS_FONT_SIZE_STEP
                    else:
                        return img.clone(), font_size
        return get_empty_image(), 0

    def get_structure_info_display(self, structure: list, index: int) -> Image:
        with Drawing() as draw:
            draw.fill_color = Color(const.TEXT_COLOR)
            draw.font_size = const.INFODISPLAY_FONT_SIZE
            draw.font = const.FONT
            for current_index, item in enumerate(structure):
                if current_index == index:
                    draw.font = const.BOLD_FONT
                    draw.text(
                        current_index * const.INFODISPLAY_ITEM_WIDTH,
                        const.INFODISPLAY_FONT_SIZE,
                        item,
                    )
                    draw.font = const.FONT
                else:
                    draw.text(
                        current_index * const.INFODISPLAY_ITEM_WIDTH,
                        const.INFODISPLAY_FONT_SIZE,
                        item,
                    )
            with Image(
                width=const.WIDTH,
                height=const.HEIGHT,
                background=Color(const.BG_COLOR),
            ) as img:
                draw(img)
                img.trim()

                return img.clone()

    def get_index(self, verse: str, font_size: int) -> Image:
        with Image(
            width=const.WIDTH,
            height=const.HEIGHT,
            background=Color(const.BG_COLOR),
        ) as img:
            img.caption(
                verse + ".",
                font=Font(
                    const.FONT_PATH,
                    size=font_size,
                    color=Color(const.TEXT_COLOR),
                ),
            )
            img.trim()
            return img.clone()
