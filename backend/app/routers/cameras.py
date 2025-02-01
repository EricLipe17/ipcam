from app.db import DBSession
from app.db.models import AudioStream, VideoStream, Camera, CameraCreate
from app.dependencies import get_current_active_user
from app.processes.camera import AVCamera
from app import process_manager
from app.settings.local import settings

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
        print("Trying to accept websocket connection.")
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


@router.websocket("/{id}/live")
async def websocket_endpoint(websocket: WebSocket, id: int):
    logger.info("Websocket endpoint hit.")
    await manager.connect(websocket)
    logger.info("Websocket connected.")
    try:
        index = 0
        while True:
            with open(
                (
                    f"/backend/out00{index}.mp4"
                    if index < 10
                    else f"/backend/out0{index}.mp4"
                ),
                "rb",
            ) as f:
                logger.info("Loading segment.")
                data = f.read()
                logger.info("Sending segment.")
                await websocket.send_bytes(data)
                logger.info("Sent segment.")
            index += 1
            logger.info("Awaiting command to send next segment.")
            cmd = await websocket.receive_text()
            print(f"\nReceived command: {cmd}\n")
    except WebSocketDisconnect:
        logger.exception("Websocket disconnected due to exception.")
        manager.disconnect(websocket)
