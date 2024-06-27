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

from os import path
from .log import error_msg


def expand_dir(directory: str) -> str:
    expanded_user_dir = path.expanduser(directory)
    expanded_user_and_env_vars_dir = path.expandvars(expanded_user_dir)
    abs_path = path.abspath(expanded_user_and_env_vars_dir)
    return abs_path


def make_sure_file_exists(filename: str) -> None:
    if not path.isfile(filename):
        try:
            with open(
                filename, mode="w+", encoding="utf-8-sig"
            ) as file_creator:
                file_creator.write("")
        except (FileNotFoundError, PermissionError, IOError) as error:
            error_msg(
                "Failed to create file in '{}'. Reason: {}".format(
                    filename, error
                )
            )
