from app.db import get_session
from app.db.models import Camera
from app.processes.messages import Message, MessageType
from app.settings.local import settings

import av
from av.container.input import InputContainer
from datetime import datetime
import logging
from multiprocessing import Process
from multiprocessing.connection import Connection
import os
import pytz
import time


class CameraProcess(Process):
    url: str
    id: int
    connection: Connection
    camera: InputContainer
    playlist_name: str
    output_kwargs: dict

    def __init__(self, url: str, id: int, connection: Connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.id = id
        self.connection = connection
        self.camera = None
        self.playlist_name = "output.m3u8"
        self.output_kwargs = {
            "mode": "w",
            "format": "hls",
            "options": {
                "hls_time": "2",
                "hls_segment_type": "mpegts",
                "hls_playlist_type": "event",
                "hls_flags": "append_list",
            },
        }

    @staticmethod
    def probe_url(url: str):
        ## TODO: Make this actuall return the audio/video stream classes instead of the av object.
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

    def _flush_stream(self, stream, output):
        for packet in stream.encode():
            output.mux(packet)

    def _get_date(self):
        return f"{datetime.now().strftime("%Y-%m-%d")}"

    def _get_path(self):
        return f"{settings.storage_dir}/cameras/{self.id}/{self._get_date()}"

    def _get_video_stream(self, output_container, input_video_stream):
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

    def _seconds_until_midnight(self):
        """Calculates the time until midnight in the specified timezone."""
        # All timezones: pytz.all_timezones
        tz = pytz.timezone(time.tzname[time.daylight])
        now = datetime.now(tz)
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        time_left = midnight - now
        return time_left.seconds

    def _get_segment_url(self):
        return f"/cameras/{self.id}/segments/{self._get_date()}/"

    def _next_playlist(self):
        return f"cameras/{self.id}/{self._get_date()}/output.m3u8"

    def _send_message(
        self,
        message,
        level=logging.INFO,
        m_type=MessageType.Error,
    ):
        self.connection.send(
            Message(
                process_id=self.id,
                process_name=self.name,
                message=message,
                level=level,
                m_type=m_type,
            )
        )

    def run(self):
        # Create av camera
        self._send_message(f"Opening.")
        self.camera = av.open(self.url)
        self._send_message(f"Successfully opened.")

        # Get the camera from the DB to update it as the recording progresses.
        self._send_message(f"Getting DB session.")
        db_session = next(get_session())
        db_cam = db_session.get(Camera, self.id)
        self._send_message(f"DB session acquired.")

        # Create the AV camera
        hls_opts = self.output_kwargs.get("options")

        # Set the HLS url to locate the video segments and create the physical storage location of the segments.
        path = self._get_path()
        hls_opts.update({"hls_base_url": self._get_segment_url()})
        os.makedirs(path, exist_ok=True)

        # Set the DB camera's active playlist and recording flag
        self._send_message(f"Setting active playlist.")
        db_cam.active_playlist = self._next_playlist()
        db_cam.is_recording = True
        db_session.commit()
        self._send_message(f"Playlist set.")

        # Open the HLS output container and begin recording data from the camera.
        self._send_message(f"Opening new output container.")
        output_container = av.open(
            **self.output_kwargs, file=f"{path}/{self.playlist_name}"
        )
        cam_video_stream = self.camera.streams.video[0]
        out_video_stream = self._get_video_stream(output_container, cam_video_stream)

        time_to_record = self._seconds_until_midnight()
        self._send_message(f"Recording.")
        for frame in self.camera.decode(cam_video_stream):
            try:
                if frame.dts is None:
                    continue

                if int(frame.time) % time_to_record == 0 and frame.time > 1:
                    # This playlist has reached it's max size, roll it over and start the next playlist.
                    self._send_message(
                        f"Playlist max size reached. Rolling over to a new playlist."
                    )
                    self._flush_stream(out_video_stream, output_container)
                    output_container.close()
                    path = self._get_path()
                    hls_opts.update({"hls_base_url": self._get_segment_url()})
                    os.makedirs(path, exist_ok=True)
                    output_container = av.open(
                        **self.output_kwargs, file=f"{path}/{self.playlist_name}"
                    )
                    out_video_stream = self._get_video_stream(
                        output_container, cam_video_stream
                    )

                    # Update the playlist in the DB camera since we are rolling it over.
                    db_cam = db_session.get(Camera, self.id)
                    db_cam.active_playlist = self._next_playlist()
                    db_session.commit()

                for packet in out_video_stream.encode(frame):
                    output_container.mux(packet)
            except Exception as e:
                self.camera.close()
                output_container.close()
                self._send_message(
                    message=f"Encountered generic exception while recording. Closing all resources and stopping.",
                    level=logging.ERROR,
                    m_type=MessageType.Error,
                )
