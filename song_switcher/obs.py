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


import obsws_python as obs

import config as const


def change_to_song_scene(song_number: int) -> None:
    cl = obs.ReqClient(
        host=const.OBS_WEBSOCKET_HOSTNAME,
        port=const.OBS_WEBSOCKET_PORT,
        password=const.OBS_WEBSOCKET_PASSWORD,
        timeout=3,
    )
    cl.set_current_program_scene(f"{const.OBS_SONG_SCENE_PREFIX}{song_number}")
