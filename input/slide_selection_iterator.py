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
from input import parse_metadata, generate_final_prompt
from slides import SlideStyle

import config as const

import slidegen


def slide_selection_iterator(
    disable_async_enabled: bool, slide_style: SlideStyle
) -> None:
    iterator_prompt = "Exit now? [y/N]: "
    structure_prompt = (
        "Choose song structure (leave blank for full song)"
        + " eg. [1,R,2,R] / [1-4]: "
    )
    rclone_local_dir = expand_dir(const.RCLONE_LOCAL_DIR)

    song_counter = 0
    while True:
        song_counter += 1
        input_prompt_prefix = "[{}{}] ".format(
            const.OBS_SUBDIR_NAMING, song_counter
        )
        prompt_answer = str(input(input_prompt_prefix + iterator_prompt))
        if prompt_answer.lower() == "y":
            create_min_obs_subdirs()
            break

        os.system(
            "cd {} && fzf {} > {}".format(
                rclone_local_dir,
                const.FZF_ARGS,
                os.path.join(
                    const.SSYNC_CACHE_DIR, const.SSYNC_CHOSEN_FILE_NAMING
                ),
            )
        )

        chosen_song_file = read_chosen_song_file()

        if len(chosen_song_file) == 0:
            log("no slides chosen, skipping...")
        else:
            src_dir = os.path.join(rclone_local_dir, chosen_song_file)
            dest_dir = create_and_get_dest_dir(
                expand_dir(const.OBS_SLIDES_DIR), song_counter
            )

            full_song_structure = get_structure_for_prompt(
                slide_style, src_dir, dest_dir
            )
            log(
                "full song structure of '{}':\n{}".format(
                    chosen_song_file,
                    full_song_structure,
                ),
                color="magenta",
            )

            structure_prompt_answer = input(
                input_prompt_prefix + structure_prompt
            ).strip()

            log(
                "generating slides '{}' to '{}{}'...".format(
                    chosen_song_file, const.OBS_SUBDIR_NAMING, song_counter
                )
            )

            generate_slides_for_selected_song(
                slide_style,
                src_dir,
                dest_dir,
                generate_final_prompt(
                    structure_prompt_answer, full_song_structure
                ),
                disable_async_enabled,
            )

    remove_chosenfile()


def generate_slides_for_selected_song(
    classic_slide_style: SlideStyle,
    src_dir: str,
    dest_dir: str,
    calculated_prompt: str | list[str],
    disable_async_enabled: bool,
) -> None:
    executing_slidegen_instance = slidegen.Slidegen(
        classic_slide_style,
        src_dir,
        dest_dir,
        calculated_prompt,
    )
    executing_slidegen_instance.execute(disable_async_enabled)


def get_structure_for_prompt(classic_slide_style, src_dir, dest_dir):
    dummy_slidegen_instance = slidegen.Slidegen(
        classic_slide_style,
        src_dir,
        dest_dir,
        "",
    )
    parse_metadata(dummy_slidegen_instance)
    full_song_structure = dummy_slidegen_instance.metadata["structure"]
    return full_song_structure


def get_file_list_inside(rclone_local_dir):
    file_list_str = ""
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
    file_list_str = file_list_str.replace("\n", "\\n")
    return file_list_str


def remove_chosenfile() -> None:
    try:
        if os.path.isfile(
            os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CHOSEN_FILE_NAMING)
        ):
            os.remove(
                os.path.join(
                    const.SSYNC_CACHE_DIR, const.SSYNC_CHOSEN_FILE_NAMING
                ),
            )
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
        os.path.join(const.SSYNC_CACHE_DIR, const.SSYNC_CHOSEN_FILE_NAMING),
        encoding="utf-8-sig",
        mode="r",
    ) as tempfile_file_opener:
        chosen_song_file = tempfile_file_opener.read()[:-1].strip()
    return chosen_song_file
