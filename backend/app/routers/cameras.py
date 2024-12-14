from app.models import AudioSteam, VideoStream, Camera, CameraIn
from app.dependencies import get_current_active_user
from app.process_manager import open_camera, get_date
from app import camera_manager
from app.settings.local import settings


from typing import Annotated, List
from fastapi import APIRouter, Depends, Header, Response, Request, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse
import random

router = APIRouter(
    prefix="/cameras",
    tags=["cameras"],
)

cameras = []


@router.get("/")
async def get_cameras(
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    print("Get cameras endpoint.")
    return cameras


@router.get("/{id}")
async def get_camera(
    id: int,
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    return cameras[id - 1]


def get_py_video_stream(id: int, cam_ref: int, av_video_stream):
    py_video_stream = VideoStream(
        id=id,
        camera_ref=cam_ref,
        codec=av_video_stream.codec.name,
        time_base=(
            av_video_stream.time_base.numerator,
            av_video_stream.time_base.denominator,
        ),
        height=av_video_stream.height,
        width=av_video_stream.width,
        sample_aspect_ratio=(
            av_video_stream.sample_aspect_ratio.numerator,
            av_video_stream.sample_aspect_ratio.denominator,
        ),
        bit_rate=av_video_stream.bit_rate,
        framerate=(
            av_video_stream.codec_context.framerate.numerator,
            av_video_stream.codec_context.framerate.denominator,
        ),
        gop_size=av_video_stream.codec_context.framerate * 10,
        pix_fmt=av_video_stream.pix_fmt,
    )
    return py_video_stream


@router.post("/add_camera")
async def add_camera(py_cam_in: CameraIn):
    # I dont like the dual return type. Need to change that

    # Check that we can query the camera and collect some metadata
    py_video_stream = None
    id = 0
    if len(cameras):
        id = cameras[-1].id + 1
    try:
        av_camera, err_msg = open_camera(py_cam_in.url)
        if err_msg:
            return Response(
                content=f"Unable to create camera: {err_msg}",
                status_code=400,
                media_type="text/plain",
            )
        av_video_stream = av_camera.streams.video[0]
        py_video_stream = get_py_video_stream(id, id, av_video_stream)
        av_camera.close()
    except Exception as e:
        return Response(
            content=f"Unable to connect to camera due to an exception: {e}.",
            status_code=500,
            media_type="text/plain",
        )

    # Open the camera, and try to start recording it's data in a separate process
    created, err = camera_manager.add_camera(id, py_cam_in.name, py_cam_in.url)
    if not created:
        return Response(
            content=f"Unable to start recording for camera at: {py_cam_in.url}. Exception: {err}",
            status_code=500,
            media_type="text/plain",
        )

    # Return the pydantic version of the created camera
    playlist_date = get_date()
    py_cam = Camera(
        id=id,
        **py_cam_in.model_dump(),
        active_playlist=f"cameras/{id}/{playlist_date}/output.m3u8",
        video=py_video_stream,
        is_recording=True,
    )
    cameras.append(py_cam)
    return py_cam


@router.get("/{id}/{date}/{playlist}")
async def get_playlist(id: str, date: str, playlist: str):
    return FileResponse(
        path=f"{settings.storage_dir}/{id}/{date}/{playlist}", filename=playlist
    )


@router.get("/{id}/segments/{date}/{segment}")
async def get_segment(id: str, date: str, segment: str):
    print(f"Segment: {segment}")
    return FileResponse(
        path=f"{settings.storage_dir}/{id}/{date}/{segment}", filename=segment
    )
