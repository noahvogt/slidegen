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

from utils import (
    log,
    create_min_obs_subdirs,
    error_msg,
    expand_dir,
)
from slides import ClassicSongTemplate, ClassicStartSlide, ClassicSongSlide
from input import parse_metadata, generate_final_prompt

import config as const

import slidegen


def slide_selection_iterator(ssync):
    iterator_prompt = "Exit now? [y/N]: "
    structure_prompt = (
        "Choose song structure (leave blank for full song)"
        + " eg. [1,R,2,R] / [1-4]: "
    )
    file_list_str = ""
    rclone_local_dir = expand_dir(const.RCLONE_LOCAL_DIR)
    obs_slides_dir = expand_dir(const.OBS_SLIDES_DIR)
    try:
        for file in os.listdir(rclone_local_dir):
            file_list_str += file + "\n"
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to access items in '{}'. Reason: {}".format(
                rclone_local_dir, error
            )
        )
    file_list_str = file_list_str[:-1]
    const.SSYNC_CHOSEN_FILE_NAMING = ".chosen-tempfile"

    index = 0
    while True:
        index += 1
        input_song_prompt = "[{}{}] ".format(const.OBS_SUBDIR_NAMING, index)
        prompt_answer = str(input(input_song_prompt + iterator_prompt))
        if prompt_answer.lower() == "y":
            create_min_obs_subdirs()
            break

        file_list_str = file_list_str.replace("\n", "\\n")
        os.system(
            'printf "{}" | fzf > {}'.format(
                file_list_str, const.SSYNC_CHOSEN_FILE_NAMING
            )
        )

        chosen_song_file = read_chosen_song_file()

        if len(chosen_song_file) == 0:
            log("no slides chosen, skipping...")
        else:
            src_dir = os.path.join(rclone_local_dir, chosen_song_file)
            dest_dir = create_and_get_dest_dir(obs_slides_dir, index)

            dummy_slidegen_instance = slidegen.Slidegen(
                ClassicSongTemplate,
                ClassicStartSlide,
                ClassicSongSlide,
                src_dir,
                dest_dir,
                "",
            )
            parse_metadata(dummy_slidegen_instance)
            full_song_structure = dummy_slidegen_instance.metadata["structure"]
            log(
                "full song structure of '{}':\n{}".format(
                    chosen_song_file,
                    full_song_structure,
                ),
                color="magenta",
            )

            structure_prompt_answer = input(
                input_song_prompt + structure_prompt
            ).strip()
            calculated_prompt = generate_final_prompt(
                structure_prompt_answer, full_song_structure
            )

            log(
                "generating slides '{}' to '{}{}'...".format(
                    chosen_song_file, const.OBS_SUBDIR_NAMING, index
                )
            )

            executing_slidegen_instance = slidegen.Slidegen(
                ClassicSongTemplate,
                ClassicStartSlide,
                ClassicSongSlide,
                src_dir,
                dest_dir,
                calculated_prompt,
            )
            executing_slidegen_instance.execute(ssync.disable_async)

    remove_chosenfile()


def remove_chosenfile() -> None:
    try:
        if os.path.isfile(const.SSYNC_CHOSEN_FILE_NAMING):
            os.remove(const.SSYNC_CHOSEN_FILE_NAMING)
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg("Failed to remove chosenfile. Reason: {}".format(error))


def create_and_get_dest_dir(obs_slides_dir, index) -> str:
    dest_dir = os.path.join(
        obs_slides_dir,
        const.OBS_SUBDIR_NAMING + str(index),
    )
    os.mkdir(dest_dir)
    return dest_dir


def read_chosen_song_file() -> str:
    with open(
        const.SSYNC_CHOSEN_FILE_NAMING, encoding="utf-8", mode="r"
    ) as tempfile_file_opener:
        chosen_song_file = tempfile_file_opener.read()[:-1].strip()
    return chosen_song_file
