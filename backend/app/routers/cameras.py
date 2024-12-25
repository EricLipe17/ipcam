from app.db import DBSession
from app.db.models import AudioStream, VideoStream, Camera, CameraCreate
from app.dependencies import get_current_active_user
from app.processes.camera import CameraProcess
from app import process_manager
from app.settings.local import settings

import logging
import os
from typing import Annotated, List
from fastapi import (
    APIRouter,
    Depends,
    Header,
    Response,
    Request,
    HTTPException,
    Form,
    Query,
)
from fastapi.responses import StreamingResponse, FileResponse
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cameras",
    tags=["cameras"],
)


@router.get("/", response_model=List[Camera])
async def get_cameras(
    db_session: DBSession,
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    cameras = db_session.exec(select(Camera).offset(offset).limit(limit)).all()
    return cameras


@router.get("/{id}", response_model=Camera)
async def get_camera(
    id: int,
    db_session: DBSession,
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    camera = db_session.get(Camera, id)
    if not camera:
        raise HTTPException(detail=f"Camera with id:{id} not found.", status_code=404)
    return camera


@router.get("/{id}/ready", response_model=Camera)
async def camera_ready(id: int, db_session: DBSession):
    camera = db_session.get(Camera, id)
    if not camera:
        raise HTTPException(detail=f"Camera with id:{id} not found.", status_code=404)

    if camera.active_playlist is None and not os.path.exists(
        f"{settings.storage_dir}/{camera.active_playlist}"
    ):
        raise HTTPException(detail="Not ready yet.", status_code=204)

    return camera


def get_py_video_stream(av_video_stream):
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


@router.post("/add_camera", response_model=Camera)
async def add_camera(py_cam_create: CameraCreate, db_session: DBSession):
    # I dont like the dual return type. Need to change that

    try:
        # Check that we can query the camera and collect some metadata. ## TODO: Change this block to "get_av_streams" to return the main audio and video streams
        av_camera, err_msg = CameraProcess.probe_url(py_cam_create.url)
        if err_msg:
            raise HTTPException(
                detail=f"Unable to create camera: {err_msg}",
                status_code=400,
            )
        av_video_stream = av_camera.streams.video[0]
        py_video_stream = get_py_video_stream(av_video_stream)
        av_camera.close()

        # Create the camera in the DB so that it's PK exists and can be ref'd by it's Audio/Video streams.
        py_cam = Camera(
            **py_cam_create.model_dump(),
            is_recording=False,
        )
        db_session.add(py_cam)
        db_session.commit()
        db_session.refresh(py_cam)

        # Start recording the camera's data in a separate process.
        err = process_manager.add_camera(
            py_cam.id, py_cam_create.name, py_cam_create.url
        )
        if err:
            # If we aren't recording, we should delete this camera from DB
            db_session.delete(py_cam)
            db_session.commit()
            raise HTTPException(
                detail=f"Unable to start recording for camera at: {py_cam_create.url}. Exception: {err}",
                status_code=500,
            )
        logger.info("Past add_camera")

        # Create the camera's associated streams.
        py_video_stream.camera_id = py_cam.id
        db_session.add(py_video_stream)
        db_session.commit()
        db_session.refresh(py_cam)
        print(f"\n\nPycam after commit: {py_cam}")

        return py_cam
    except Exception as e:
        db_session.delete(py_cam)
        db_session.commit()
        logger.exception("Unable to connect to camera due to generic exception.")
        raise HTTPException(
            detail=f"Unable to connect to camera due to generic exception: {e}.",
            status_code=500,
        )


@router.get("/{id}/{date}/{playlist}")
async def get_playlist(id: str, date: str, playlist: str):
    return FileResponse(
        path=f"{settings.storage_dir}/cameras/{id}/{date}/{playlist}", filename=playlist
    )


@router.get("/{id}/segments/{date}/{segment}")
async def get_segment(id: str, date: str, segment: str):
    print(f"Segment: {segment}")
    return FileResponse(
        path=f"{settings.storage_dir}/cameras/{id}/{date}/{segment}", filename=segment
    )
