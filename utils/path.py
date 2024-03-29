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


def expand_dir(directory: str) -> str:
    expanded_user_dir = os.path.expanduser(directory)
    expanded_user_and_env_vars_dir = os.path.expandvars(expanded_user_dir)
    abs_path = os.path.abspath(expanded_user_and_env_vars_dir)
    return abs_path
