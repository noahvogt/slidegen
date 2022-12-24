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
from wand.drawing import Drawing
from wand.color import Color
from wand.font import Font

from utils import get_empty_image

import config as const

from .song_template import SongTemplate


class ClassicSongTemplate(SongTemplate):
    def __init__(self) -> None:
        self.song_template = ""

    def get_base_image(self) -> Image:
        with Image(
            width=const.WIDTH,
            height=const.HEIGHT,
            background=Color(const.BG_COLOR),
        ) as img:
            return img.clone()

    def get_titlebar_rectangle(self, text: str) -> Image:
        font_size = const.MAX_TITLE_FONT_SIZE
        while font_size >= const.MIN_TITLE_FONT_SIZE:
            with Image(
                width=const.WIDTH,
                height=const.TITLE_HEIGHT,
                background=Color(const.FG_COLOR),
            ) as img:
                img.caption(
                    text,
                    font=Font(
                        const.BOLD_FONT_PATH,
                        size=font_size,
                        color=Color(const.TITLE_COLOR),
                    ),
                )
                img.trim()
                img.border(color=Color(const.FG_COLOR), width=30, height=0)
                trimmed_img_width = img.width
                trimmed_img_height = img.height
                concat_height = int(
                    (const.TITLE_HEIGHT - trimmed_img_height) / 2
                )
                correction_heigt = (
                    const.TRIANGLE_HEIGTH
                    - trimmed_img_height
                    - (2 * concat_height)
                )
                concatenated_img = Image(
                    width=trimmed_img_width,
                    height=concat_height,
                    background=Color(const.FG_COLOR),
                )
                concatenated_img.sequence.append(img)
                concatenated_img.sequence.append(
                    Image(
                        width=trimmed_img_width,
                        height=concat_height + correction_heigt,
                        background=Color(const.FG_COLOR),
                    )
                )
                concatenated_img.concat(stacked=True)
                if concatenated_img.width > (
                    const.WIDTH - const.PLAYER_WIDTH - const.TRIANGLE_WIDTH
                ):
                    font_size -= const.TITLE_FONT_SIZE_STEP
                    continue

                return concatenated_img.clone()
        return get_empty_image()

    def get_template(self, title: str) -> Image:
        titlebar_rectangle = self.get_titlebar_rectangle(title)
        titlebar_rectangle.sequence.append(self.get_titlebar_triangle())
        titlebar_rectangle.concat(stacked=False)
        base_img = self.get_base_image()
        base_img.composite(titlebar_rectangle, top=const.TITLEBAR_Y)
        self.song_template = base_img.clone()
        return base_img.clone()

    def get_titlebar_triangle(self) -> Image:
        with Drawing() as draw:
            draw.fill_color = Color(const.FG_COLOR)
            draw.path_start()
            draw.path_move(to=(const.TRIANGLE_WIDTH, 0))
            draw.path_line(to=(0, 0))
            draw.path_line(to=(0, const.TRIANGLE_HEIGTH))
            draw.path_close()
            draw.path_finish()

            with Image(
                width=const.TRIANGLE_WIDTH,
                height=const.TRIANGLE_HEIGTH,
                background=Color(const.BG_COLOR),
            ) as img:
                draw(img)
                return img.clone()
