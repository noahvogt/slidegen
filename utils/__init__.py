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

from .audio import get_wave_duration_in_secs, get_wave_duration_in_frames
from .log import error_msg, warn, log, CustomException
from .strings import (
    get_songtext_by_structure,
    structure_as_list,
    get_unique_structure_elements,
)
from .img import get_empty_image
from .create_min_obs_subdirs import create_min_obs_subdirs
from .clear_obs_slides_dir import clear_obs_slides_dir
from .path import expand_dir
from .date import get_yyyy_mm_dd_date, get_unix_milis
from .scripts import (
    make_sure_file_exists,
    switch_to_song,
    is_valid_cd_record_checkfile,
    burn_cds_of_day,
    mark_end_of_recording,
    cycle_to_song_direction,
    SongDirection,
    make_sure_there_is_no_ongoing_cd_recording,
    get_possible_sermon_segments_of_day,
    get_segments_with_suitable_time,
    upload_sermon_segment,
    choose_cd_day,
    choose_sermon_day,
    upload_sermon_for_day,
)
