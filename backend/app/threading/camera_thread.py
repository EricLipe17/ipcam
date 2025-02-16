import threading
from app.db import get_session
from app.db.models import AudioStream, VideoStream, Camera
from app.processes.messages import Message
from app.processes.enums import MessageType, ProcessType
from app.settings import settings

import av
from av.container.input import InputContainer
from av.container.output import OutputContainer
from av.stream import Stream
from datetime import datetime
import logging
from multiprocessing import Process
from multiprocessing.connection import Connection
import os
import pytz
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session
import time


av.logging.set_level(av.logging.ERROR)


def get_py_video_stream(av_video_stream):
    """Get DB representation of av video stream."""
    if not av_video_stream:
        return None
    sample_aspect_ratio = av_video_stream.sample_aspect_ratio
    py_video_stream = VideoStream(
        codec=av_video_stream.codec.name,
        time_base_num=av_video_stream.time_base.numerator,
        time_base_den=av_video_stream.time_base.denominator,
        height=av_video_stream.height,
        width=av_video_stream.width,
        sample_aspect_ratio_num=(
            sample_aspect_ratio.numerator if sample_aspect_ratio else 16
        ),
        sample_aspect_ratio_den=(
            sample_aspect_ratio.denominator if sample_aspect_ratio else 9
        ),
        bit_rate=av_video_stream.bit_rate,
        framerate=av_video_stream.codec_context.framerate.numerator
        // av_video_stream.codec_context.framerate.denominator,
        gop_size=av_video_stream.codec_context.framerate.numerator * 10,
        pix_fmt=av_video_stream.pix_fmt,
    )
    return py_video_stream


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


def probe_camera(url: str):
    """Try to open connection to camera and return audio/video metadata upon success."""
    av_camera = None
    av_audio_stream = None
    av_video_stream = None
    py_audio_stream = None
    py_video_stream = None
    try:
        # TODO: handle rtsp over udp
        av_camera = av.open(url, options={"rtsp_transport": "tcp"})
        av_video_stream = av_camera.streams.best("video")
        av_audio_stream = av_camera.streams.best("audio")
        py_video_stream = get_py_video_stream(av_video_stream)
        py_audio_stream = get_py_audio_stream(av_audio_stream)
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
    finally:
        if av_camera is not None:
            av_camera.close()


class CameraBaseThread(threading.Thread):
    url: str
    id: int
    connection: Connection
    camera: InputContainer
    force_transcode: bool
    output_container: OutputContainer
    output_streams: dict[int, Stream]
    output_kwargs: dict
    db_session: Session
    proc_type: ProcessType
    logger: logging.Logger

    def __init__(
        self,
        url: str,
        id: int,
        connection: Connection,
        force_transcode: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.id = id
        self.connection = connection
        self.camera = None
        self.force_transcode = force_transcode
        self.output_streams = dict()
        self.output_container = None
        self.output_kwargs = dict()
        self.db_session = None
        self.proc_type = ProcessType.AVCamera
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(f"camera_{id}")

    def _remux(self):
        raise NotImplementedError("This method must be implemented by a subclass.")

    def _transcode(self):
        raise NotImplementedError("This method must be implemented by a subclass.")

    def run(self):
        raise NotImplementedError("This method must be implemented by a subclass.")

    def stop(self):
        """Stop the camera recording."""
        self._stop_event.set()

    def _flush_streams(self):
        """Flush all data in the streams."""
        for stream in self.output_streams.values():
            for packet in stream.encode():
                self.output_container.mux(packet)

    def _get_date(self):
        """Get date string: '%Y-%m-%d'."""
        return f"{datetime.now().strftime("%Y-%m-%d")}"

    def _get_path(self):
        """Get path to store segments for current playlist."""
        return f"{settings.storage_dir}/cameras/{self.id}/segments/{self._get_date()}"

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
        self.logger.log(level=level, msg=message)

    def _get_bitrate(self, input_stream):
        if input_stream.bit_rate:
            return input_stream.bit_rate

        if input_stream.type == "video":
            # Use the Kush Gauge to calculate bitrate for video
            # The general expectation is there is not a lot of motion in the cameras view.
            motion_complexity = 1.1
            return (
                input_stream.codec_context.framerate
                * input_stream.height
                * input_stream.width
                * motion_complexity
                * 0.07
            )
        else:
            # Default to 128 Kb/s since we are streaming and not audiophiles.
            return 128000

    def _set_best_streams(self):
        self.output_streams.clear()
        in_best_video = self.camera.streams.best("video")
        in_best_audio = self.camera.streams.best("audio")

        if self.force_transcode:
            out_best_video = self.output_container.add_stream(codec_name="h264")
            out_best_video.height = in_best_video.height
            out_best_video.width = in_best_video.width
            out_best_video.sample_aspect_ratio = in_best_video.sample_aspect_ratio
            out_best_video.codec_context.framerate = (
                in_best_video.codec_context.framerate
            )
            out_best_video.codec_context.gop_size = (
                in_best_video.codec_context.framerate * 2
            )
            out_best_video.pix_fmt = in_best_video.pix_fmt
            out_best_video.time_base = in_best_video.time_base
            out_best_video.bit_rate = self._get_bitrate(in_best_video)
            self.output_streams[in_best_video.index] = out_best_video

            if in_best_audio is not None:
                out_best_audio = self.output_container.add_stream(codec_name="aac")
                out_best_audio.time_base = in_best_audio.time_base
                out_best_audio.rate = in_best_audio.rate
                out_best_audio.sample_rate = in_best_audio.sample_rate
                out_best_audio.layout = in_best_audio.layout
                out_best_audio.format = in_best_audio.format
                out_best_audio.bit_rate = self._get_bitrate(in_best_audio)
                self.output_streams[in_best_audio.index] = out_best_audio
        else:
            out_best_video = self.output_container.add_stream(template=in_best_video)
            self.output_streams[in_best_video.index] = out_best_video

            if in_best_audio is not None:
                out_best_audio = self.output_container.add_stream(
                    template=in_best_audio
                )
                self.output_streams[in_best_audio.index] = out_best_audio

    def close(self):
        """Close all av resources."""
        db_cam = self.db_session.get(Camera, self.id)
        db_cam.is_recording = False
        self.db_session.commit()
        self.camera.close()
        self.output_container.close()


class SegmentCamera(CameraBaseThread):
    def __init__(
        self,
        url: str,
        id: int,
        connection: Connection,
        force_transcode: bool = False,
        *args,
        **kwargs,
    ):
        super().__init__(url, id, connection, force_transcode, *args, **kwargs)
        self.output_kwargs = {
            "mode": "w",
            "format": "segment",
            "options": {
                "segment_time": "10",
                "segment_format_options": "movflags=frag_keyframe+empty_moov+default_base_moof+faststart",
                "flags": "+cgop",
                "g": "200",  # FPS * segment_time
            },
        }

    def _remux(self):
        for packet in self.camera.demux():
            try:
                stream = self.output_streams.get(packet.stream_index, None)
                if stream:
                    packet.stream = stream
                    self.output_container.mux(packet)
            except SQLAlchemyError:
                self._send_message(
                    f"Encountered a sqlalchemy error while remuxing, continuing to record.",
                    level=logging.WARNING,
                )
            except av.FFmpegError as e:
                self.close()
                self._send_message(
                    message=(
                        "Encountered Ffmpeg exception while remuxing the recording. "
                        f"Closing all resources and stopping. \n{e}"
                    ),
                    level=logging.ERROR,
                    m_type=MessageType.Error,
                )
                raise e
            except Exception as e:
                self.close()
                self._send_message(
                    message=f"Encountered generic exception while remuxing recording. Closing all resources and stopping. \n{e}",
                    level=logging.ERROR,
                    m_type=MessageType.Error,
                )
                raise e

    def _transcode(self):
        pass

    def run(self):
        """Start recording the camera's data."""
        # Create av camera
        self._send_message(f"Opening.")
        # TODO: handle rtsp over udp
        self.camera = av.open(self.url, options={"rtsp_transport": "tcp"})
        self._send_message(f"Successfully opened.")

        # Get the camera from the DB to update it as the recording progresses.
        self._send_message(f"Getting DB session.")
        self.db_session = next(get_session())
        py_cam = self.db_session.get(Camera, self.id)
        self._send_message(f"DB session acquired.")

        # Set the physical storage location of the segments.
        path = self._get_path()
        os.makedirs(path, exist_ok=True)

        # Set the DB camera's recording flag
        py_cam.is_recording = True
        self.db_session.commit()

        # Open the output container and begin recording data from the camera.
        self._send_message(f"Opening new output container.")
        self.output_container = av.open(**self.output_kwargs, file=f"{path}/%05d.mp4")
        self._set_best_streams()

        self._send_message(f"Recording.")
        if self.force_transcode:
            self._send_message(
                "Transcoding camera data to x264 and AAC for video and audio respectively."
            )
            self._transcode()
        else:
            self._send_message("Remuxing camera data for camera.")
            self._remux()
