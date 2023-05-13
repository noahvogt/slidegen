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

import argparse
from dataclasses import dataclass

from utils import log, error_msg, expand_dir


def parse_slidegen_argv_as_tuple() -> tuple:
    parser = argparse.ArgumentParser(
        prog="slidegen", description="slidegen - a slide generator."
    )
    parser.add_argument(
        "songfile",
        type=str,
        help="the input text file (with header and body)",
    )
    parser.add_argument(
        "output",
        type=str,
        help="output directory where the generated slides are placed",
    )
    parser.add_argument(
        "structure",
        type=str,
        help="the chosen song structure",
        nargs="?",
        default="",
    )

    args = parser.parse_args()

    try:
        song_file_path = expand_dir(args.songfile)
        output_dir = expand_dir(args.output)
    except IndexError:
        error_msg("incorrect amount of arguments provided, exiting...")
    try:
        chosen_structure = args.structure
        if chosen_structure.strip() == "":
            chosen_structure = ""
    except IndexError:
        chosen_structure = ""

    log("parsing '{}'...".format(song_file_path))
    return song_file_path, output_dir, chosen_structure


def parse_ssync_args_as_tuple() -> tuple:
    parser = argparse.ArgumentParser(
        prog="ssync",
        description="ssync - an interactive program syncing that lets "
        + "you choose songs to generate slides for using fzf.",
    )
    parser.add_argument(
        "-o", "--offline", help="skips syncing with remote", action="store_true"
    )
    parser.add_argument(
        "-s",
        "--sequential",
        help="disables async slide generation",
        action="store_true",
    )
    args = parser.parse_args()
    return args.offline, args.sequential


@dataclass
class SsyncFlags:
    offline_enabled: bool
    disable_async_enabled: bool
