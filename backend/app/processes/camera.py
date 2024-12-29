from app.db import get_session
from app.db.models import AudioStream, VideoStream, Camera
from app.processes.messages import Message
from app.processes.enums import MessageType, ProcessType
from app.settings.local import settings

import av
from av.container.input import InputContainer
from datetime import datetime
import logging
from multiprocessing import Process
from multiprocessing.connection import Connection
import os
import pytz
from sqlalchemy.exc import SQLAlchemyError
import time


class CameraProcess(Process):
    url: str
    id: int
    connection: Connection
    camera: InputContainer
    playlist_name: str
    output_kwargs: dict
    proc_type: ProcessType

    def __init__(self, url: str, id: int, connection: Connection, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.id = id
        self.connection = connection
        self.camera = None
        self.output_container = None
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
        self.proc_type = ProcessType.Camera

    @staticmethod
    def get_py_video_stream(av_video_stream):
        """Get DB representation of av video stream."""
        if not av_video_stream:
            return None
        py_video_stream = VideoStream(
            codec=av_video_stream.codec.name,
            time_base_num=av_video_stream.time_base.numerator,
            time_base_den=av_video_stream.time_base.denominator,
            height=av_video_stream.height,
            width=av_video_stream.width,
            sample_aspect_ratio_num=av_video_stream.sample_aspect_ratio.numerator,
            sample_aspect_ratio_den=av_video_stream.sample_aspect_ratio.denominator,
            bit_rate=av_video_stream.bit_rate,
            framerate=av_video_stream.codec_context.framerate.numerator
            // av_video_stream.codec_context.framerate.denominator,
            gop_size=av_video_stream.codec_context.framerate.numerator * 10,
            pix_fmt=av_video_stream.pix_fmt,
        )
        return py_video_stream

    @staticmethod
    def get_py_audio_stream(av_audio_stream):
        """Get DB representation of the av audio stream."""
        # TODO: Implement this correctly
        if not av_audio_stream:
            return None
        py_audio_stream = AudioStream(
            codec="aac",
            time_base_den=1,
            time_base_num=1,
            sample_rate=1,
            layout_name="radio",
            format_name="aac",
        )
        return py_audio_stream

    @staticmethod
    def probe_camera(url: str):
        """Try to open connection to camera and return audio/video metadata upon success."""
        av_camera = None
        py_video_stream = None
        py_audio_stream = None
        try:
            av_camera = av.open(url)
            av_video_stream = av_camera.streams.best("video")
            av_audio_stream = av_camera.streams.best("audio")
            py_video_stream = CameraProcess.get_py_video_stream(av_video_stream)
            py_audio_stream = CameraProcess.get_py_audio_stream(av_audio_stream)
            return (py_video_stream, py_audio_stream, "")
        except av.OSError:
            return (
                py_video_stream,
                py_audio_stream,
                "Input/output error. The provided url could not be opened.",
            )
        except av.FFmpegError as e:
            return (py_video_stream, py_audio_stream, e.strerror)
        except Exception as e:
            return (
                py_video_stream,
                py_audio_stream,
                f"An unknown exception occurred: {e}",
            )

    def _flush_stream(self, stream, output):
        """Flush all data in the stream."""
        for packet in stream.encode():
            output.mux(packet)

    def _get_date(self):
        """Get date string: '%Y-%m-%d'."""
        return f"{datetime.now().strftime("%Y-%m-%d")}"

    def _get_path(self):
        """Get path to store segments for current playlist."""
        return f"{settings.storage_dir}/cameras/{self.id}/segments/{self._get_date()}"

    def _get_segment_url(self):
        """Get the segment url for the HLS playlist."""
        return f"/cameras/{self.id}/segments/{self._get_date()}/"

    def _next_playlist(self):
        """Get the next active HLS playlist."""
        return f"cameras/{self.id}/{self._get_date()}/output.m3u8"

    def _get_video_stream(self, input_video_stream):
        """Get new av video stream from an input stream template."""
        stream = self.output_container.add_stream(codec_name="h264", options={})
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

    def _send_message(
        self,
        message,
        level=logging.INFO,
        m_type=MessageType.Log,
    ):
        """Send a message to the manager."""
        self.connection.send(
            Message(
                process_id=self.id,
                process_name=self.name,
                message=message,
                level=level,
                m_type=m_type,
            )
        )

    def close(self, db_session):
        """Close all av resources."""
        db_cam = db_session.get(Camera, self.id)
        db_cam.is_recording = False
        db_session.commit()
        self.camera.close()
        self.output_container.close()

    def run(self):
        """Start recording the camera's data."""
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
        self.output_container = av.open(
            **self.output_kwargs, file=f"{path}/{self.playlist_name}"
        )
        cam_video_stream = self.camera.streams.video[0]
        out_video_stream = self._get_video_stream(cam_video_stream)

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
                    self._send_message(f"Flushing streams.")
                    self._flush_stream(out_video_stream, self.output_container)
                    self.output_container.close()
                    path = self._get_path()
                    hls_opts.update({"hls_base_url": self._get_segment_url()})
                    os.makedirs(path, exist_ok=True)

                    self._send_message(f"Opening new output container.")
                    self.output_container = av.open(
                        **self.output_kwargs, file=f"{path}/{self.playlist_name}"
                    )
                    out_video_stream = self._get_video_stream(cam_video_stream)

                    # Update the playlist in the DB camera since we are rolling it over.
                    self._send_message(f"Updating DB with new info.")
                    db_cam = db_session.get(Camera, self.id)
                    db_cam.active_playlist = self._next_playlist()
                    db_session.commit()

                for packet in out_video_stream.encode(frame):
                    self.output_container.mux(packet)
            except SQLAlchemyError:
                self._send_message(
                    f"Encountered a sqlalchemy error, continuing to record.",
                    level=logging.WARNING,
                )
            except av.FFmpegError as e:
                self.close(db_session)
                self._send_message(
                    message=f"Encountered Ffmpeg exception while recording. Closing all resources and stopping. \n{e}",
                    level=logging.ERROR,
                    m_type=MessageType.Error,
                )
            except Exception as e:
                self.close(db_session)
                self._send_message(
                    message=f"Encountered generic exception while recording. Closing all resources and stopping. \n{e}",
                    level=logging.ERROR,
                    m_type=MessageType.Error,
                )
