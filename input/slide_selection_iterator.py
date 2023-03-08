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

import os

from utils import log, create_min_obs_subdirs
from slides import ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide

import config as const

import slidegen


def slide_selection_iterator():
    iterator_prompt = "Exit now? [y/N]: "
    structure_prompt = (
        "Choose song structure (leave blank for full song)"
        + " eg. [1,R,2,R] / [1-4]: "
    )
    file_list_str = ""
    for file in os.listdir(const.RCLONE_LOCAL_DIR):
        file_list_str += file + "\n"
    file_list_str = file_list_str[:-1]
    tempfile_str = ".chosen-tempfile"

    index = 0
    while True:
        index += 1
        input_song_prompt = "[{} {}] ".format(const.OBS_TARGET_SUBDIR, index)
        prompt_answer = str(input(input_song_prompt + iterator_prompt))
        if prompt_answer.lower() == "y":
            create_min_obs_subdirs(index)
            break

        file_list_str = file_list_str.replace("\n", "\\n")
        os.system('printf "{}" | fzf > {}'.format(file_list_str, tempfile_str))

        with open(
            tempfile_str, encoding="utf-8", mode="r"
        ) as tempfile_file_opener:
            chosen_song_file = tempfile_file_opener.read()[:-1].strip()

        if len(chosen_song_file) == 0:
            log("no slides chosen, skipping...")
        else:
            structure_prompt_answer = input(
                input_song_prompt + structure_prompt
            )

            log(
                "generating slides '{}' to '{} {}'...".format(
                    chosen_song_file, const.OBS_TARGET_SUBDIR, index
                )
            )
            src_dir = os.path.join(const.RCLONE_LOCAL_DIR, chosen_song_file)
            dest_dir = os.path.join(
                const.OBS_SLIDES_DIR,
                const.OBS_TARGET_SUBDIR + " " + str(index),
            )
            os.mkdir(dest_dir)

            slidegen_instance = slidegen.Slidegen(
                ClassicSongTemplate,
                ClassicStartSlide,
                ClassicSongSlide,
                src_dir,
                dest_dir,
                structure_prompt_answer,
            )
            slidegen_instance.execute()

    if os.path.isfile(tempfile_str):
        os.remove(tempfile_str)
