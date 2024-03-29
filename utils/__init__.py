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

from .log import error_msg, log
from .strings import (
    get_songtext_by_structure,
    structure_as_list,
    get_unique_structure_elements,
)
from .img import get_empty_image
from .create_min_obs_subdirs import create_min_obs_subdirs
from .clear_obs_slides_dir import clear_obs_slides_dir
from .path import expand_dir
from .date import calculate_yyyy_mm_dd_date
from .songchooser import make_sure_cachefile_exists, switch_to_song
