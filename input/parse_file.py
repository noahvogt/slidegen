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

from re import match

from utils import (
    error_msg,
    structure_as_list,
    get_unique_structure_elements,
    get_songtext_by_structure,
    expand_dir,
)

import config as const


def parse_metadata(slidegen) -> None:
    metadata_dict = dict.fromkeys(const.METADATA_STRINGS)
    try:
        with open(
            slidegen.song_file_path, mode="r", encoding="utf-8-sig"
        ) as opener:
            content = opener.readlines()
    except IOError:
        error_msg(
            "could not read the the song input file: '{}'".format(
                slidegen.song_file_path
            )
        )
    valid_metadata_strings = list(const.METADATA_STRINGS)

    for line_nr, line in enumerate(content):
        if len(valid_metadata_strings) == 0:
            content = content[line_nr:]
            break
        if not match(
            r"^(?!structure)\S+: .+|^structure: ([0-9]+|R)(,([0-9]+|R))*$",
            line,
        ):
            if line[-1] == "\n":
                line = line[:-1]
            missing_metadata_strs = ""
            for metadata_str in valid_metadata_strings:
                missing_metadata_strs += ", " + metadata_str
            missing_metadata_strs = missing_metadata_strs[2:]
            error_msg(
                "invalid metadata syntax on line {}:\n{}\nThe ".format(
                    line_nr + 1, line
                )
                + "following metadata strings are still missing: {}".format(
                    missing_metadata_strs
                )
            )
        metadata_str = line[: line.index(":")]
        if metadata_str in valid_metadata_strings:
            metadata_dict[metadata_str] = line[line.index(": ") + 2 : -1]
            valid_metadata_strings.remove(metadata_str)
            continue

        error_msg("invalid metadata string '{}'".format(metadata_str))

    slidegen.metadata = metadata_dict
    slidegen.song_file_content = content


def parse_songtext(slidegen) -> None:
    unique_structures = get_unique_structure_elements(
        structure_as_list(slidegen.metadata["structure"])
    )
    output_dict = dict.fromkeys(unique_structures)

    for structure in unique_structures:
        output_dict[structure] = get_songtext_by_structure(
            slidegen.song_file_content, structure
        )

    slidegen.songtext = output_dict


def get_cachefile_content(cachefile: str) -> list:
    expanded_path = expand_dir(cachefile)
    try:
        with open(
            expanded_path, mode="r", encoding="utf-8-sig"
        ) as cachefile_reader:
            cachefile_content = cachefile_reader.readlines()
    except (FileNotFoundError, PermissionError, IOError) as error:
        error_msg(
            "Failed to access cachefile in '{}'. Reason: {}".format(
                expanded_path, error
            )
        )
    return cachefile_content
