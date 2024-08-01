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

from flask import Flask, render_template_string

import config as const
from input import get_cachefile_content
from utils import get_unix_milis

from .verify import ongoing_cd_recording_detected, calc_cuesheet_timestamp

cd_recording_status_webserver = Flask(__name__)


def get_cd_marker_count(active_recording: bool, cachefile_content: list) -> int:
    if not active_recording:
        return 0

    return int(cachefile_content[1].strip())


def get_cd_count(active_recording: bool, cachefile_content: list) -> int:
    if not active_recording:
        return 0

    return int(cachefile_content[5].strip())


def get_full_rec_time(active_recording: bool, cachefile_content: list) -> str:
    if not active_recording:
        return "00:00"

    return calc_cuesheet_timestamp(
        int(cachefile_content[3].strip()), get_unix_milis()
    )[:5]


def get_track_rec_time(active_recording: bool, cachefile_content: list) -> str:
    if not active_recording:
        return "00:00"

    return calc_cuesheet_timestamp(
        int(cachefile_content[4].strip()), get_unix_milis()
    )[:5]


@cd_recording_status_webserver.route("/")
def index():
    recording_active = ongoing_cd_recording_detected()
    cachefile_content = get_cachefile_content(
        const.CD_RECORD_CACHEFILE, suppress_error=True
    )
    cd_marker_count = get_cd_marker_count(recording_active, cachefile_content)
    cd_count = get_cd_count(recording_active, cachefile_content)
    cd_rec_time = get_full_rec_time(recording_active, cachefile_content)
    track_rec_time = get_track_rec_time(recording_active, cachefile_content)

    background_color = "green" if recording_active else "grey"

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CD Recording Status</title>
        <style>
            body {{
                background-color: {background_color};
                color: white;
                text-align: center;
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                overflow: hidden;
            }}
            .content {{
                font-size: 4vw; /* Responsive font size */
                text-align: center;
                max-width: 90vw; /* Prevents overflow on very large text */
            }}
            p {{
                margin: 0.5em 0;
            }}
            .timestamp {{
                font-family: monospace;
            }}
        </style>
        <script>
            setTimeout(function() {{
                window.location.reload(1);
            }}, 300);
        </script>
    </head>
    <body>
        <div class="content">
            <h1>CD Recording Status</h1>
            <p>Recording is currently {'active' if recording_active else 'not active'}.</p>
            <p>{f"CD Count: {cd_count}" if recording_active else '&ZeroWidthSpace;'}</p>
            <p>{f"CD Marker Count: {cd_marker_count}" if recording_active else '&ZeroWidthSpace;'}</p>
            <p>{f"Recording Time: <span class=timestamp>{cd_rec_time}</span> (Track: <span class=timestamp>{track_rec_time})</span>" if recording_active else '&ZeroWidthSpace;'}</p>
        </div>
    </body>
    </html>
    """

    return render_template_string(html)
