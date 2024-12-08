from app.models import AudioSteam, VideoStream, Camera
from app.dependencies import get_current_active_user

import av
import socket
import io
from typing import Annotated, List
from fastapi import APIRouter, Depends, Header, Response, Request, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
import random

router = APIRouter(prefix="/cameras", tags=["cameras"],)
CHUNK_SIZE = 1024*1024*2
audio = AudioSteam(id=1, camera_ref=1, codec="aac", time_base=(1, 1), sample_rate=41400,
                   layout_name="stereo", format_name="fltp")
video = VideoStream(id=1, camera_ref=1, codec="h264", time_base=(1, 1), height=1920, width=1080, sample_aspect_ratio=(16, 9),
                    bit_rate=10400, framerate=(25, 1), gop_size=250, pix_fmt="yuv420")

cam = Camera(id=1, url="rtsp://{ip_address}:8554/city-traffic",
             active_playlist=f"cameras/1/2024-12-07-39/output.m3u8", video=video)

cameras = [cam]

BASE_STORAGE_PATH ="/backend/app/cameras"

@router.get("/")
async def get_cameras(
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    print("Get cameras endpoint.")
    return cameras

@router.get("/{id}")
async def get_camera(id: int,
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    camera = cameras[id - 1]
    camera.active_playlist = f"cameras/1/2024-12-08-47/output.m3u8" if random.randint(0, 1) % 2 else "cameras/1/2024-12-07-39/output.m3u8"
    return cameras[id - 1]

def generate_segment():
    print("Inside generate segment")
    ip_address = socket.gethostbyname('rtsp-server')
    camera = av.open(f"rtsp://{ip_address}:8554/city-traffic")
    count = 1
    while True:
      print(f"Generating chunk: {count}")
      output_buffer = io.BytesIO()
      output = av.open(output_buffer, 'w', format="mp4")
      video_stream = camera.streams.video[0]
      stream = output.add_stream(template=video_stream)
      it = camera.demux(video_stream)
      packet = next(it)
      total_size = 0
      while total_size <= CHUNK_SIZE:
        # We need to skip the "flushing" packets that `demux` generates.
        if packet.dts is None:
            packet = next(it)
            continue
        total_size += packet.buffer_size
        # We need to assign the packet to the new stream.
        packet.stream = stream
        output.mux(packet)
        packet = next(it)

      output.close()
      byte_buf = output_buffer.getvalue()
      output_buffer.close()
      count += 1
    # return byte_buf
      yield byte_buf

    # with open("output.mp4", "wb") as f:
    #   f.write(output_buffer.getbuffer())

@router.get("/{id}/{date}/{playlist}")
async def get_playlist(id: str, date: str, playlist: str):
   return FileResponse(path=f"{BASE_STORAGE_PATH}/{id}/{date}/{playlist}", filename=playlist)

@router.get("/{id}/segments/{date}/{segment}")
async def get_segment(id: str, date: str, segment: str):
   print(f"Segment: {segment}")
   return FileResponse(path=f"{BASE_STORAGE_PATH}/{id}/{date}/{segment}", filename=segment)
