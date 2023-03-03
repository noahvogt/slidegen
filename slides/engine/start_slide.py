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

from wand.exceptions import BlobError

from utils import (
    log,
    error_msg,
)

import config as const


def generate_start_slide(slidegen, template_img, zfill_length) -> None:
    log("generating start slide...")

    first_slide = slidegen.start_slide_form()
    start_slide_img = first_slide.get_slide(
        template_img,
        slidegen.metadata["book"],
        slidegen.metadata["text"],
        slidegen.metadata["melody"],
    )
    start_slide_img.format = const.IMAGE_FORMAT
    try:
        start_slide_img.save(
            filename=path.join(
                slidegen.output_dir,
                const.FILE_NAMEING
                + "1".zfill(zfill_length)
                + "."
                + const.FILE_EXTENSION,
            )
        )
    except BlobError:
        error_msg("could not write start slide to target directory")
