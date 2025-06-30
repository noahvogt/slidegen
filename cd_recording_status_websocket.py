#!/usr/bin/env python3

import asyncio
import json
from os import path

import websockets

from utils import expand_dir, get_current_yyyy_mm_dd_date, log
import config as const
from input import get_cachefile_content
from recording import (
    is_valid_cd_record_checkfile,
    get_is_recording_active,
    get_cd_count,
    get_cd_marker_count,
    get_full_rec_time,
    get_track_rec_time,
)


def get_inactive_recording_status() -> dict:
    return {
        "recording": False,
        "cd": 0,
        "track": 0,
        "cd_time": "00:00",
        "track_time": "00:00",
    }


async def status_sender(websocket):
    while True:
        if path.isfile(expand_dir(const.CD_RECORD_CACHEFILE)):
            cachefile_content = get_cachefile_content(const.CD_RECORD_CACHEFILE)
            if is_valid_cd_record_checkfile(
                cachefile_content, get_current_yyyy_mm_dd_date()
            ):
                is_recording_active = get_is_recording_active(cachefile_content)
                status = {
                    "recording": is_recording_active,
                    "cd": get_cd_count(is_recording_active, cachefile_content),
                    "track": get_cd_marker_count(
                        is_recording_active, cachefile_content
                    ),
                    "cd_time": get_full_rec_time(
                        is_recording_active, cachefile_content
                    ),
                    "track_time": get_track_rec_time(
                        is_recording_active, cachefile_content
                    ),
                }
            else:
                status = get_inactive_recording_status()
        else:
            status = get_inactive_recording_status()
        await websocket.send(json.dumps(status))
        await asyncio.sleep(const.CD_RECORD_WEBSOCKET_SLEEP)


async def handler(websocket):
    log(f"Client connected: {websocket.remote_address}")
    try:
        await status_sender(websocket)
    except websockets.exceptions.ConnectionClosed:
        log("Client disconnected")


async def main():
    log(
        "Starting CD Rec status WebSocket server on ws://"
        + f"{const.CD_RECORD_WEBSOCKET_HOST}:{const.CD_RECORD_WEBSOCKET_PORT}"
    )
    async with websockets.serve(
        handler, const.CD_RECORD_WEBSOCKET_HOST, const.CD_RECORD_WEBSOCKET_PORT
    ):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(main())
