from app.db import DBSession
from app.db.models import AudioStream, VideoStream, Camera, CameraCreate
from app.dependencies import get_current_active_user
from app.processes.camera import AVCamera
from app import process_manager
from app.settings import settings

import logging
import os
from typing import Annotated, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import FileResponse
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
async def ready(id: int, db_session: DBSession):
    camera = db_session.get(Camera, id)
    if not camera:
        raise HTTPException(detail=f"Camera with id:{id} not found.", status_code=404)

    if camera.active_playlist is None:
        raise HTTPException(detail="Not ready yet.", status_code=204)

    playlist_dir = f"{settings.storage_dir}/{camera.active_playlist}".rsplit("/", 1)[0]
    num_files = len(os.listdir(playlist_dir))
    if num_files < 3:
        raise HTTPException(detail="Not ready yet.", status_code=204)

    return camera


@router.post("/add_camera", response_model=Camera)
async def add_camera(py_cam_create: CameraCreate, db_session: DBSession):
    try:
        # Check that we can query the camera and collect some metadata. ## TODO: Change this block to "get_av_streams" to return the main audio and video streams
        py_video_stream, py_audio_stream, err_msg = AVCamera.probe_camera(
            py_cam_create.url
        )
        if err_msg:
            raise HTTPException(
                detail=f"Unable to create camera: {err_msg}",
                status_code=400,
            )

        # Create the camera in the DB so that it's PK exists and can be ref'd by it's Audio/Video streams.
        py_cam = Camera(
            **py_cam_create.model_dump(),
            is_recording=False,
        )
        py_cam.video_stream = py_video_stream
        if py_audio_stream is not None:
            py_cam.audio_stream = py_audio_stream
        db_session.add(py_cam)
        db_session.commit()
        db_session.refresh(py_cam)

        # Start recording the camera's data in a separate process.
        err = process_manager.add_camera(py_cam)
        if err:
            # If we aren't recording, we should delete this camera from DB
            if py_cam in db_session:
                db_session.delete(py_cam)
                db_session.commit()
            raise HTTPException(
                detail=f"Unable to start recording for camera at: {py_cam_create.url}. Exception: {err}",
                status_code=500,
            )

        return py_cam
    except Exception as e:
        if py_cam in db_session:
            db_session.delete(py_cam)
            db_session.commit()
        logger.exception("Unable to connect to camera due to generic exception.")
        raise HTTPException(
            detail=f"Unable to connect to camera due to generic exception: {e}.",
            status_code=500,
        )


@router.get("/{id}/segments/{date}/{playlist}")
async def get_playlist(id: int, date: str, playlist: str):
    return FileResponse(
        path=f"{settings.storage_dir}/cameras/{id}/segments/{date}/{playlist}",
        filename=playlist,
    )


@router.get("/{id}/segment")
async def get_segment(id: int, date: str, filename: str):
    return FileResponse(
        path=f"{settings.storage_dir}/cameras/{id}/segments/{date}/{filename}",
        filename=filename,
    )


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()
import time
from datetime import datetime


def get_latest_segment(id: int):
    # If we return the absolute newest segment, we will run into timing issues with the frontend causing buffer loading
    # choppy streaming.
    path = f"{settings.storage_dir}/cameras/{id}/segments/{datetime.now().strftime("%Y-%m-%d")}"
    segments = os.listdir(path)
    segments.sort()
    return f"{path}/{segments[-2]}"


@router.websocket("/{id}/live")
async def websocket_endpoint(websocket: WebSocket, id: int):
    # TODO: update endpoint to get the latest segment from the segment directory
    await manager.connect(websocket)
    try:
        index = 0

        prev_segment = get_latest_segment(id)
        while True:
            latest_segment = get_latest_segment(id)
            logger.info(f"\nlatest_segment: {latest_segment}")
            if prev_segment != latest_segment:
                prev_segment = latest_segment
                index = 0
            with open(
                latest_segment,
                "rb",
            ) as f:
                data = f.read()
                await websocket.send_bytes(data)
                time.sleep(10)
            index += 1
            cmd = await websocket.receive_text()
            logger.info(f"cmd: {cmd}\n")
    except WebSocketDisconnect:
        logger.info("Client closed livestream.")
        manager.disconnect(websocket)
