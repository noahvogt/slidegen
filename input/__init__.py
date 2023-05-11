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

from .parse_prompt import parse_prompt_input
from .parse_file import (
    parse_metadata,
    parse_songtext,
    get_songchooser_cachefile_content,
)
from .parse_argv import parse_argv_as_tuple
from .parse_argv import parse_ssync_args
from .validate_config import validate_ssync_config, validate_songchooser_config
from .slide_selection_iterator import slide_selection_iterator
