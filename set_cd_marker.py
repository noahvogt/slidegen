#!/usr/bin/env python3

"""
Copyright © 2024 Noah Vogt <noah@noahvogt.com>

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

from os import path, mkdir
from shlex import split
from subprocess import Popen

from utils import (
    get_yyyy_mm_dd_date,
    make_sure_file_exists,
    is_valid_cd_record_checkfile,
    get_unix_milis,
    log,
    warn,
    error_msg,
    expand_dir,
    mark_end_of_recording,
)
from input import get_cachefile_content, validate_cd_record_config
import config as const


def start_cd_recording() -> None:
    cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    date = get_yyyy_mm_dd_date()
    cd_num = int(cachefile_content[5].strip())

    ensure_output_dir_exists(date)

    while cachefile_content[1].strip() != "9001":
        filename = path.join(
            const.CD_RECORD_OUTPUT_BASEDIR,
            date,
            f"{date}-{cd_num:0{const.CD_RECORD_FILENAME_ZFILL}}.wav",
        )

        unix_milis = get_unix_milis()

        log(f"starting cd #{cd_num} recording...")
        cmd = "ffmpeg -y {} -ar 44100 -t {} {}".format(
            const.CD_RECORD_FFMPEG_INPUT_ARGS,
            const.CD_RECORD_MAX_SECONDS,
            filename,
        )
        process = Popen(split(cmd))

        cachefile = expand_dir(const.CD_RECORD_CACHEFILE)
        log("updating active ffmpeg pid")
        try:
            with open(
                cachefile, mode="w+", encoding="utf-8-sig"
            ) as file_writer:
                file_writer.write(cachefile_content[0].strip() + "\n")
                # reset marker to 1
                file_writer.write("1\n")
                file_writer.write(f"{process.pid}\n")
                file_writer.write(f"{unix_milis}\n")
                file_writer.write(f"{unix_milis}\n")
                file_writer.write(f"{cd_num}\n")
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to write to cachefile '{}'. Reason: {}".format(
                    cachefile, error
                )
            )
        fresh_cachefile_content = get_cachefile_content(
            const.CD_RECORD_CACHEFILE
        )
        update_cue_sheet(
            fresh_cachefile_content, date, unix_milis, initial_run=True
        )

        _ = process.communicate()[0]  # wait for subprocess to end
        cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
        cd_num += 1
        if process.returncode not in [255, 0]:
            mark_end_of_recording(cachefile_content)
            error_msg(f"ffmpeg terminated with exit code {process.returncode}")


def ensure_output_dir_exists(date):
    cue_sheet_dir = path.join(expand_dir(const.CD_RECORD_OUTPUT_BASEDIR), date)
    try:
        if not path.exists(cue_sheet_dir):
            mkdir(cue_sheet_dir)
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to create to cue sheet directory '{}'. Reason: {}".format(
                cue_sheet_dir, error
            )
        )


def create_cachefile_for_marker(
    cachefile_content: list,
    yyyy_mm_dd: str,
    unix_milis: int,
    initial_run=False,
) -> None:
    cachefile = expand_dir(const.CD_RECORD_CACHEFILE)
    if initial_run:
        marker = 1
    else:
        marker = int(cachefile_content[1]) + 1
        if marker > 99:
            return

    if (
        not (initial_run)
        and unix_milis - int(cachefile_content[4])
        < const.CD_RECORD_MIN_TRACK_MILIS
    ):
        return

    log("writing cd marker {} to cachefile...".format(marker))
    try:
        with open(cachefile, mode="w+", encoding="utf-8-sig") as file_writer:
            file_writer.write(f"{yyyy_mm_dd}\n")
            file_writer.write(f"{marker}\n")
            if initial_run:
                file_writer.write("000\n")  # fake pid, gets overriden later
                file_writer.write(f"{unix_milis}\n")
            else:
                file_writer.write(f"{cachefile_content[2].strip()}\n")
                file_writer.write(f"{cachefile_content[3].strip()}\n")
            file_writer.write(f"{unix_milis}\n")
            if initial_run:
                file_writer.write("1\n")
            else:
                file_writer.write(f"{cachefile_content[5].strip()}\n")
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to write to cachefile '{}'. Reason: {}".format(
                cachefile, error
            )
        )


def update_cue_sheet(
    cachefile_content: list, yyyy_mm_dd: str, unix_milis: int, initial_run=False
) -> None:
    cue_sheet_dir = path.join(
        expand_dir(const.CD_RECORD_OUTPUT_BASEDIR), yyyy_mm_dd
    )
    # use current cachefile data for here cd_num only
    fresh_cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    cd_num = (
        fresh_cachefile_content[5].strip().zfill(const.CD_RECORD_FILENAME_ZFILL)
    )
    cue_sheet_path = path.join(cue_sheet_dir, f"sheet-{cd_num}.cue")
    wave_path = path.join(cue_sheet_dir, f"{yyyy_mm_dd}-{cd_num}.wav")
    if initial_run:
        log("updating cue sheet...")
        try:
            if not path.exists(cue_sheet_dir):
                mkdir(cue_sheet_dir)
            with open(
                cue_sheet_path, mode="w+", encoding="utf-8-sig"
            ) as file_writer:
                file_writer.write(f'FILE "{wave_path}" WAVE\n')
                file_writer.write("  TRACK 01 AUDIO\n")
                file_writer.write("    INDEX 01 00:00:00\n")
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to write to cue sheet file '{}'. Reason: {}".format(
                    cue_sheet_path, error
                )
            )
    else:
        marker = int(cachefile_content[1]) + 1
        if marker > 99:
            warn("An Audio CD can only hold up to 99 tracks.")
            return

        start_milis = int(cachefile_content[3])
        last_track_milis = int(cachefile_content[4])
        if unix_milis - last_track_milis < const.CD_RECORD_MIN_TRACK_MILIS:
            warn(
                "Minimum track length of {}ms not satisfied".format(
                    const.CD_RECORD_MIN_TRACK_MILIS
                )
            )
            return

        milis_diff = unix_milis - start_milis
        mins = milis_diff // 60000
        milis_diff -= 60000 * mins
        secs = int(milis_diff / 1000)
        milis_diff -= 1000 * secs
        frames = int(75 / 1000 * milis_diff)

        log("updating cue sheet...")
        try:
            with open(
                cue_sheet_path, mode="a", encoding="utf-8-sig"
            ) as file_writer:
                file_writer.write("  TRACK {:02d} AUDIO\n".format(marker))
                file_writer.write(
                    "    INDEX 01 {:02d}:{:02d}:{:02d}\n".format(
                        mins, secs, frames
                    )
                )
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to write to cue sheet file '{}'. Reason: {}".format(
                    cue_sheet_path, error
                )
            )


def set_cd_marker() -> None:
    cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
    yyyy_mm_dd = get_yyyy_mm_dd_date()
    unix_milis = get_unix_milis()
    cachefile_and_time_data = (cachefile_content, yyyy_mm_dd, unix_milis)

    if is_valid_cd_record_checkfile(*cachefile_and_time_data[:-1]):
        create_cachefile_for_marker(*cachefile_and_time_data)
        update_cue_sheet(*cachefile_and_time_data)
    else:
        create_cachefile_for_marker(*cachefile_and_time_data, initial_run=True)
        update_cue_sheet(*cachefile_and_time_data, initial_run=True)
        start_cd_recording()


def main() -> None:
    validate_cd_record_config()
    make_sure_file_exists(const.CD_RECORD_CACHEFILE)
    set_cd_marker()


if __name__ == "__main__":
    main()
