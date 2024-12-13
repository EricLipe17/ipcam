import av
import socket
import os
import av.container
import pytz
from datetime import datetime
import time
import multiprocessing as mp
from multiprocessing.connection import Connection

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

def new_cam(id: int, camera, connection: Connection):
  # ip_address = socket.gethostbyname('localhost')
  # camera = av.open(f"rtsp://{ip_address}:8554/city-traffic")
  playlist_name = "output.m3u8"
  kwargs = {"mode":'w', "format":"hls",
            "options":{"hls_time": "10",
                       "hls_segment_type": "mpegts",
                       "hls_playlist_type":"event"
                       }}
  hls_opts = kwargs.get('options')

  path, date = get_path(id)
  hls_opts.update({'hls_base_url': f'/cameras/{id}/segments/{date}/'})
  os.makedirs(path)

  output_container = av.open(**kwargs, file=f"{path}/{playlist_name}")
  cam_video_stream = camera.streams.video[0]
  out_video_stream = create_video_stream(output_container, cam_video_stream)

  time_to_record = seconds_until_midnight()
  for frame in camera.decode(cam_video_stream):
    try:
      if frame.dts is None:
        continue

      if int(frame.time) % time_to_record == 0 and frame.time > 1:
        flush_stream(out_video_stream, output_container)
        output_container.close()
        path, date = get_path(id)
        hls_opts.update({'hls_base_url': f'/cameras/{id}/segments/{date}/'})
        os.makedirs(path)
        output_container = av.open(**kwargs, file=f"{path}/{playlist_name}")
        out_video_stream = create_video_stream(output_container, cam_video_stream)

      for packet in out_video_stream.encode(frame):
        output_container.mux(packet)
    except Exception:
      output_container.close()
      camera.close()

class CameraProcessManager:
  def __init__(self):
    self.context = mp.get_context('fork')
    self.processes = dict()
    self.connections = dict()

  def add_camera(self, id: int, name: str, camera):
    if name in self.processes:
      raise ValueError(f"Cannot create process with name: {name} because it already exists!")

    parent_conn, child_conn = mp.Pipe()
    kwargs = {'id': id, 'camera': camera, 'connection': child_conn}

    p = self.context.Process(name=name, target=new_cam,
                             kwargs=kwargs, daemon=True)
    self.processes[name] = p
    self.connections[name] = parent_conn

    p.start()






# def target(name="DEFAULT NAME"):
#   import os
#   print(f"My name is: {name}, My ID is: {os.getpid()}")

# def target2():
#   raise Exception("I died on purpose")

# if __name__ == '__main__':
#   pm = ProcessManager()
#   pm.add_process("t1", target=target, kwargs={'name': "t1"})
#   pm.add_process("t2", target=target, kwargs={})
#   pm.add_process("t3", target=target2, kwargs={})

#   for p in pm.processes.values():
#     print(f"{p.name} is alive: {p.is_alive()}")
#     p.join()
