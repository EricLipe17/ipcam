import asyncio
import av
from datetime import datetime
import multiprocessing as mp
from multiprocessing.connection import Connection
import os
import pytz
import time

from app.db import get_session
from app.db.models import Camera
from app.settings.local import settings


def flush_stream(stream, output):
    for packet in stream.encode():
        output.mux(packet)


def get_date():
    return f"{datetime.now().strftime("%Y-%m-%d")}"


def get_path(id: int):
    date = get_date()
    return f"{settings.storage_dir}/{id}/{date}", date


def create_video_stream(output_container, input_video_stream):
    stream = output_container.add_stream(codec_name="h264", options={})
    # The options are required for transcoding to work
    stream.height = input_video_stream.height
    stream.width = input_video_stream.width
    stream.sample_aspect_ratio = input_video_stream.sample_aspect_ratio
    stream.codec_context.framerate = input_video_stream.codec_context.framerate
    stream.codec_context.gop_size = 10 * stream.codec_context.framerate
    stream.pix_fmt = input_video_stream.pix_fmt
    stream.time_base = input_video_stream.time_base
    return stream


def seconds_until_midnight():
    """Calculates the time until midnight in the specified timezone."""
    # All timezones: pytz.all_timezones
    tz = pytz.timezone(time.tzname[time.daylight])
    now = datetime.now(tz)
    midnight = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    time_left = midnight - now
    return time_left.seconds


def open_camera(url: str):
    camera = None
    try:
        camera = av.open(url)
        return (camera, "")
    except av.OSError:
        return (camera, "Input/output error. The provided url could not be opened.")
    except av.FFmpegError as e:
        return (camera, e.strerror)
    except Exception as e:
        return (camera, "An unknown exception occurred.")


def record(id: int, url: str, connection: Connection):
    # Get the camera from the DB to update it as the recording progresses.
    db_session = next(get_session())
    db_cam = db_session.get(Camera, id)

    # Create the AV camera
    camera = av.open(url)
    playlist_name = "output.m3u8"
    kwargs = {
        "mode": "w",
        "format": "hls",
        "options": {
            "hls_time": "10",
            "hls_segment_type": "mpegts",
            "hls_playlist_type": "event",
            "hls_flags": "append_list",
        },
    }
    hls_opts = kwargs.get("options")

    # Set the HLS url to locate the video segments and create the physical storage location of the segments.
    path, date = get_path(id)
    hls_opts.update({"hls_base_url": f"/cameras/{id}/segments/{date}/"})
    os.makedirs(path, exist_ok=True)

    # Set the DB camera's active playlist and recording flag
    db_cam.active_playlist = f"cameras/{id}/{date}/output.m3u8"
    db_cam.is_recording = True
    db_session.commit()

    # Open the HLS output container and begin recording data from the camera.
    output_container = av.open(**kwargs, file=f"{path}/{playlist_name}")
    cam_video_stream = camera.streams.video[0]
    out_video_stream = create_video_stream(output_container, cam_video_stream)

    time_to_record = seconds_until_midnight()
    connection.send("Begining recording.")
    for frame in camera.decode(cam_video_stream):
        try:
            if frame.dts is None:
                continue

            if int(frame.time) % time_to_record == 0 and frame.time > 1:
                # This playlist has reached it's max size, roll it over and start the next playlist.
                flush_stream(out_video_stream, output_container)
                output_container.close()
                path, date = get_path(id)
                hls_opts.update({"hls_base_url": f"/cameras/{id}/segments/{date}/"})
                os.makedirs(path, exist_ok=True)
                output_container = av.open(**kwargs, file=f"{path}/{playlist_name}")
                out_video_stream = create_video_stream(
                    output_container, cam_video_stream
                )

                # Update the playlist in the DB camera since we are rolling it over.
                db_cam = db_session.get(Camera, id)
                db_cam.active_playlist = f"cameras/{id}/{date}/output.m3u8"
                db_session.commit()

            for packet in out_video_stream.encode(frame):
                output_container.mux(packet)
        except Exception as e:
            connection.send(f"Camera died with the following exception: {str(e)}")
            with open("record.log", "a") as log:
                log.write(f"{str(e)}\n")
                log.write("Cleaning up resources in record method.444\n\n\n")
                camera.close()
                output_container.close()
                exit(1)


class CameraProcessManager:
    def __init__(self):
        self.context = mp.get_context("spawn")
        self.processes = dict()
        self.connections = dict()
        self.wait_for = 0.1

    def add_camera(self, id: int, name: str, url: str):
        p = None
        try:
            if name in self.processes:
                return f"Cannot create process with name: {name} because it already exists!"
            print(f"adding new camera with id: {id}")

            parent_conn, child_conn = mp.Pipe()
            kwargs = {"id": id, "url": url, "connection": child_conn}
            p = self.context.Process(
                name=name, target=record, kwargs=kwargs, daemon=True
            )
            p.start()
            self.processes[name] = p
            self.connections[name] = parent_conn
            return None
        except Exception as e:
            if p and p.is_alive():
                p.kill()
            print(e)
            return f"Caught exception trying to start the recording: {e}"

    async def poll_cameras(self):
        print("Inside poll_cameras")
        log = open("record.log", "a")
        while True:
            for camera, connection in self.connections.items():
                if connection.poll():
                    obj = connection.recv()
                    print(f"Printing to console: {obj}")
                    log.write(f"Received message from {camera}. ")
                    log.write(f"{obj}\n")
                    log.flush()
            await asyncio.sleep(self.wait_for)
