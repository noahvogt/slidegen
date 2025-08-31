# Copyright © 2025 Noah Vogt <noah@noahvogt.com>

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

import sys

from PyQt5.QtWidgets import (  # pylint: disable=no-name-in-module
    QApplication,
    QMessageBox,
)

from utils import log, error_msg, InfoMsgBox
import config as const


def validate_ssync_config() -> None:
    needed_constants: dict = {
        "RCLONE_LOCAL_DIR": const.RCLONE_LOCAL_DIR,
        "RCLONE_REMOTE_DIR": const.RCLONE_REMOTE_DIR,
        "SSYNC_CHECKFILE_NAMING": const.SSYNC_CHECKFILE_NAMING,
        "SSYNC_CACHEFILE_NAMING": const.SSYNC_CACHEFILE_NAMING,
        "SSYNC_CACHE_DIR": const.SSYNC_CACHE_DIR,
        "OBS_SLIDES_DIR": const.OBS_SLIDES_DIR,
        "OBS_SUBDIR_NAMING": const.OBS_SUBDIR_NAMING,
        "OBS_MIN_SUBDIRS": const.OBS_MIN_SUBDIRS,
        "SSYNC_CHOSEN_FILE_NAMING": const.SSYNC_CHOSEN_FILE_NAMING,
        "SSYNC_SLIDESHOW_INPUT_NAMING": const.SSYNC_SLIDESHOW_INPUT_NAMING,
        "OBS_WEBSOCKET_HOSTNAME": const.OBS_WEBSOCKET_HOSTNAME,
        "OBS_WEBSOCKET_PORT": const.OBS_WEBSOCKET_PORT,
    }
    general_config_validator(needed_constants)


def validate_obs_song_scene_switcher_config() -> None:
    needed_constants: dict = {
        "NEXTSONG_CACHE_FILE": const.NEXTSONG_CACHE_FILE,
        "OBS_MIN_SUBDIRS": const.OBS_MIN_SUBDIRS,
        "OBS_WEBSOCKET_HOSTNAME": const.OBS_WEBSOCKET_HOSTNAME,
        "OBS_WEBSOCKET_PORT": const.OBS_WEBSOCKET_PORT,
        "OBS_SONG_SCENE_PREFIX": const.OBS_SONG_SCENE_PREFIX,
    }
    general_config_validator(needed_constants, gui_error_out=True)


def validate_obs_song_slides_switcher_config() -> None:
    needed_constants: dict = {
        "NEXTSONG_CACHE_FILE": const.NEXTSONG_CACHE_FILE,
        "SSYNC_SLIDESHOW_INPUT_NAMING": const.SSYNC_SLIDESHOW_INPUT_NAMING,
        "OBS_WEBSOCKET_HOSTNAME": const.OBS_WEBSOCKET_HOSTNAME,
        "OBS_WEBSOCKET_PORT": const.OBS_WEBSOCKET_PORT,
        "OBS_SONG_SCENE_PREFIX": const.OBS_SONG_SCENE_PREFIX,
    }

    general_config_validator(needed_constants, gui_error_out=True)


def validate_autoprint_infomail_config() -> None:
    needed_constants: dict = {
        "AUTOPRINT_INFOMAIL_CMD": const.AUTOPRINT_INFOMAIL_CMD,
        "AUTOPRINT_INFOMAIL_DATEFILE": const.AUTOPRINT_INFOMAIL_DATEFILE,
    }
    general_config_validator(needed_constants, gui_error_out=True)


def validate_cd_burn_config() -> None:
    needed_constants: dict = {
        "CD_RECORD_CACHEFILE": const.CD_RECORD_CACHEFILE,
        "CD_RECORD_OUTPUT_BASEDIR": const.CD_RECORD_OUTPUT_BASEDIR,
    }
    general_config_validator(needed_constants, gui_error_out=True)


def validate_cd_record_config() -> None:
    validate_cd_burn_config()

    needed_constants: dict = {
        "CD_RECORD_FFMPEG_INPUT_ARGS": const.CD_RECORD_FFMPEG_INPUT_ARGS,
        "CD_RECORD_MAX_SECONDS": const.CD_RECORD_MAX_SECONDS,
        "CD_RECORD_MIN_TRACK_MILIS": const.CD_RECORD_MIN_TRACK_MILIS,
    }
    general_config_validator(needed_constants, gui_error_out=True)


def validate_manual_filedrop_sermon_upload_config() -> None:
    needed_constants: dict = {
        "SERMON_UPLOAD_USE_FTP": const.SERMON_UPLOAD_USE_FTP,
        "SERMON_UPLOAD_SUITABLE_SEGMENT_FRAMES": const.SERMON_UPLOAD_SUITABLE_SEGMENT_FRAMES,
    }
    general_config_validator(needed_constants, gui_error_out=True)
    if const.SERMON_UPLOAD_USE_FTP:
        needed_constants: dict = {
            "SERMON_UPLOAD_USE_FTP": const.SERMON_UPLOAD_USE_FTP,
            "SERMON_UPLOAD_FTP_HOSTNAME": const.SERMON_UPLOAD_FTP_HOSTNAME,
            "SERMON_UPLOAD_FTP_USER": const.SERMON_UPLOAD_FTP_USER,
            "SERMON_UPLOAD_FTP_PASSWORD": const.SERMON_UPLOAD_FTP_PASSWORD,
            "SERMON_UPLOAD_FTP_UPLOAD_DIR": const.SERMON_UPLOAD_FTP_UPLOAD_DIR,
        }
        general_config_validator(needed_constants, gui_error_out=True)
    else:
        needed_constants: dict = {
            "SERMON_UPLOAD_WPSM_API_BASE_URL": const.SERMON_UPLOAD_WPSM_API_BASE_URL,
            "SERMON_UPLOAD_WPSM_USER": const.SERMON_UPLOAD_WPSM_USER,
            "SERMON_UPLOAD_WPSM_PASSWORD": const.SERMON_UPLOAD_WPSM_PASSWORD,
        }
        general_config_validator(needed_constants, gui_error_out=True)


def validate_sermon_upload_config() -> None:
    validate_cd_burn_config()
    validate_manual_filedrop_sermon_upload_config()


def general_config_validator(
    needed_constants: dict, gui_error_out=False
) -> None:
    for key in needed_constants:
        if needed_constants.get(key) == "":
            msg = "needed config entry '{}' is empty".format(key)
            if not gui_error_out:
                error_msg(msg)
            app = QApplication
            InfoMsgBox(QMessageBox.Critical, "Error", msg)
            del app
            sys.exit(1)

    log("configuration initialised")
