from app.models import AudioSteam, VideoStream, Camera, CameraIn
from app.dependencies import get_current_active_user
from app.process_manager import open_camera, get_date
from app import camera_manager
from app.settings.local import settings


from typing import Annotated, List
from fastapi import APIRouter, Depends, Header, Response, Request, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
import random

router = APIRouter(prefix="/cameras", tags=["cameras"],)

#### FAKE CONFIG DATA
# audio = AudioSteam(id=1, camera_ref=1, codec="aac", time_base=(1, 1), sample_rate=41400,
#                    layout_name="stereo", format_name="fltp")
# video = VideoStream(id=1, camera_ref=1, codec="h264", time_base=(1, 1), height=1920, width=1080, sample_aspect_ratio=(16, 9),
#                     bit_rate=10400, framerate=(25, 1), gop_size=250, pix_fmt="yuv420")

# cam = Camera(id=1, url="rtsp://{ip_address}:8554/city-traffic",
#              active_playlist=f"cameras/1/2024-12-07-39/output.m3u8", video=video)
cameras = []
####

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

@router.post("/add_camera")
async def add_camera(py_cam_in: CameraIn):
  av_camera, err_msg = open_camera(py_cam_in.url)
  if err_msg:
     return Response(content=f"Unable to create camera: {err_msg}", status_code=400, media_type="text/plain")

  id = 0
  if len(cameras):
     id = cameras[-1].id + 1

  camera_manager.add_camera(id, py_cam_in.name, av_camera)

  playlist_date = get_date()

  av_input_vstream = av_camera.streams.video[0]
  py_video_stream = VideoStream(id=id, camera_ref=id, codec=av_input_vstream.codec.name,
                                time_base=(av_input_vstream.time_base.numerator,
                                           av_input_vstream.time_base.denominator),
                                height=av_input_vstream.height, width=av_input_vstream.width,
                                sample_aspect_ratio=(av_input_vstream.sample_aspect_ratio.numerator,
                                                      av_input_vstream.sample_aspect_ratio.denominator),
                                bit_rate=av_input_vstream.bit_rate,
                                framerate=(av_input_vstream.codec_context.framerate.numerator,
                                            av_input_vstream.codec_context.framerate.denominator),
                                gop_size=av_input_vstream.codec_context.framerate * 10,
                                pix_fmt=av_input_vstream.pix_fmt)

  py_cam = Camera(id=id, **py_cam_in.model_dump(), active_playlist=f"cameras/{id}/{playlist_date}/output.m3u8",
                   video=py_video_stream, is_recording=True)
  cameras.append(py_cam)
  return py_cam

@router.get("/{id}/{date}/{playlist}")
async def get_playlist(id: str, date: str, playlist: str):
   return FileResponse(path=f"{settings.storage_dir}/{id}/{date}/{playlist}", filename=playlist)

@router.get("/{id}/segments/{date}/{segment}")
async def get_segment(id: str, date: str, segment: str):
   print(f"Segment: {segment}")
   return FileResponse(path=f"{settings.storage_dir}/{id}/{date}/{segment}", filename=segment)
