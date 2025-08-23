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

from threading import Thread
from os import path, utime
from pathlib import Path
from re import compile
import datetime

from wand.exceptions import BlobError

from utils import (
    log,
    error_msg,
)

import config as const


# used in attempt to get a correct ordering as obs image slide shows ignores
# filenames, but it appearently also ignores a/m-times as seen in
# https://github.com/obsproject/obs-studio/issues/10382
def fix_timestamps(slidegen):
    log("fixing timestamps...")

    folder = Path(slidegen.output_dir).resolve()

    pattern = compile(rf"{const.FILE_NAMING}(\d+)\.jpg$")

    slides = []
    for f in folder.iterdir():
        m = pattern.match(f.name)
        if m:
            num = int(m.group(1))
            slides.append((num, f))

    slides.sort(key=lambda x: x[0])

    base_date = datetime.date(2000, 1, 1)

    for i, (num, file_path) in enumerate(slides, start=1):
        new_date = base_date + datetime.timedelta(days=i - 1)
        new_dt = datetime.datetime.combine(new_date, datetime.time(12, 0, 0))
        ts = new_dt.timestamp()

        utime(file_path, (ts, ts))


def generate_slides(
    slidegen, slide_count, template_img, zfill_length, disable_async: bool
) -> list[Thread]:
    log("generating song slides...")

    current_slide_index: int = 0

    log("spawning subprocess for start slide...", color="yellow")

    threads = [
        Thread(
            target=generate_start_slide,
            args=(slidegen, template_img, zfill_length, disable_async),
        )
    ]

    for index, structure in enumerate(slidegen.chosen_structure):
        structure_element_splitted: list = slidegen.songtext[
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
                "spawning subprocess for song slide [{} / {}]...".format(
                    current_slide_index, slide_count
                ),
                color="yellow",
            )

            if inner_slide_count == 1:
                structure_element_value: str = slidegen.songtext[structure]
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

            threads.append(
                Thread(
                    target=generate_song_slide,
                    args=(
                        slidegen.slide_style.song_slide_form,
                        template_img,
                        structure_element_value,
                        slidegen,
                        index,
                        inner_slide_count,
                        inner_slide,
                        current_slide_index,
                        zfill_length,
                        disable_async,
                    ),
                )
            )

    for thread in threads:
        thread.start()

    return threads


def generate_start_slide(slidegen, template_img, zfill_length, disable_async):
    first_slide = slidegen.slide_style.start_slide_form()
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
                const.FILE_NAMING
                + "1".zfill(zfill_length)
                + "."
                + const.FILE_EXTENSION,
            )
        )
        if disable_async:
            log("start slide generated and saved")
    except BlobError:
        error_msg("could not write start slide to target directory")


def generate_song_slide(
    song_slide,
    template_img,
    structure_element_value,
    slidegen,
    index,
    inner_slide_count,
    inner_slide,
    current_slide_index,
    zfill_length,
    disable_async,
):
    song_slide_img = song_slide.get_slide(
        self=slidegen.slide_style.song_slide_form(),
        template_img=template_img,
        slide_text=structure_element_value,
        song_structure=slidegen.chosen_structure,
        index=index,
        use_arrow=bool(
            inner_slide_count != 1 and inner_slide != inner_slide_count - 1
        ),
    )
    song_slide_img.format = const.IMAGE_FORMAT
    try:
        song_slide_img.save(
            filename=path.join(
                slidegen.output_dir,
                const.FILE_NAMING
                + str(current_slide_index + 1).zfill(zfill_length)
                + "."
                + const.FILE_EXTENSION,
            )
        )
        if disable_async:
            log("song slide {} generated and saved".format(current_slide_index))
    except BlobError:
        error_msg(
            "could not write song slide {} to target directory".format(
                current_slide_index
            )
        )
