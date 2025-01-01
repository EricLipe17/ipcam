import asyncio
import logging
import multiprocessing as mp
from multiprocessing.connection import Connection
from sqlmodel import select
from typing import List, Dict

from app.db import get_session
from app.db.models import Camera
from app.processes import AVCamera
from app.processes.enums import MessageType, ProcessType

logger = logging.getLogger(__name__)

if mp.get_start_method() != "spawn":
    logger.warning(
        f"\nForcing multiprocessing to spawn instead of {mp.get_start_method()}.\n"
    )
    mp.set_start_method("spawn", force=True)


class ProcessManager:
    processes: Dict[int, mp.Process]
    connections: Dict[int, Connection]
    restarts = List[int]
    retries: Dict[int, int]
    sleep: float

    def __init__(self):
        self.processes = dict()
        self.connections = dict()
        self.retries = dict()
        self.restarts = list()
        self.sleep = 0.5
        self.max_restarts = 10

    def start_processes(self):
        db_session = next(get_session())

        self._start_camera_processes(db_session)

    def _start_camera_processes(self, db_session):
        stmt = select(Camera).where(Camera.is_recording == True)
        cameras = db_session.exec(stmt)
        for camera in cameras:
            self.add_camera(id=camera.id, name=camera.name, url=camera.url)

    def add_process(self, id: int, connection: Connection, process: mp.Process):
        """
        Add a generic process and it's parent connection to the process pool. @process must be a subclass of
        mp.Process so that it can define the member `proc_type`.
        """
        try:
            if not process.is_alive():
                process.start()
        except Exception:
            logger.exception(
                f"Encountered exception when adding process:{process.proc_type} with ID:{id} to the process pool."
            )
            if process.is_alive():
                process.kill()
        else:
            self.processes[id] = process
            self.connections[id] = connection
            self.retries[id] = 0
            return None

    def add_camera(self, py_cam: Camera):
        """Create and add a camera process to the process pool."""
        try:
            if id in self.processes:
                return f"Cannot create process with id:{id} because it already exists!"
            logger.info(f"Adding new camera with id:{id}.")

            parent_conn, child_conn = mp.Pipe()
            camera = AVCamera(
                name=py_cam.name,
                id=py_cam.id,
                url=py_cam.url,
                force_transcode=py_cam.force_transcode,
                connection=child_conn,
                daemon=True,
            )
            camera.start()
        except Exception:
            if camera and camera.is_alive():
                logger.warning(
                    f"Camera recording process for id:{py_cam.id} was alive but killing it due to unknown exception."
                )
                camera.kill()
            msg = f"Caught exception trying to start the recording."
            logger.exception(msg)
            return msg
        else:
            self.processes[py_cam.id] = camera
            self.connections[py_cam.id] = parent_conn
            self.retries[py_cam.id] = 0
            return None

    def _copy_process(self, dead_proc, new_conn):
        """Create a copy of a dead process based on the process type."""
        match dead_proc.proc_type:
            case ProcessType.AVCamera:
                new_camera = AVCamera(
                    url=dead_proc.url,
                    id=dead_proc.id,
                    force_transcode=dead_proc.force_transcode,
                    connection=new_conn,
                    daemon=True,
                )
                return new_camera
            case _:
                logger.error(
                    "Received an unknown ProcessType to copy. No copy occurred."
                )
                return None

    async def _poll_restarts(self):
        """Coroutine to restart dead processes."""
        while True:
            for id in self.restarts:
                try:
                    self.retries[id] += 1
                    dead_proc = self.processes.pop(id)
                    logger.info(
                        f"Trying to restart process:{dead_proc.proc_type}, ID: {id}."
                    )
                    self.connections.pop(id)

                    parent_conn, child_conn = mp.Pipe()
                    new_proc = self._copy_process(dead_proc, child_conn)
                    new_proc.start()
                except Exception:
                    logger.exception(
                        f"Fatal error: Unable to restart process:{dead_proc.proc_type} with ID:{id}."
                    )
                    if new_proc and new_proc.is_alive():
                        new_proc.kill()
                else:
                    logger.info(
                        f"Process:{new_proc.proc_type}, ID:{id} successfully restarted."
                    )
                    self.processes[new_proc.id] = new_proc
                    self.connections[new_proc.id] = parent_conn
            self.restarts.clear()
            await asyncio.sleep(self.sleep * 10)

    async def _poll_processes(self):
        """Coroutine to poll process' for messages."""
        while True:
            try:
                for id, connection in self.connections.items():
                    if connection.poll():
                        message = connection.recv()
                        message.handle()
                        if message.m_type == MessageType.Error:
                            if self.retries.get(id) < self.max_restarts:
                                self.restarts.append(id)
                                logger.warning(
                                    f"Encountered error with ID:{id}. Process has been "
                                    f"restarted {self.retries.get(id)} times"
                                )
                            else:
                                logger.error(
                                    f"Process with ID:{id} has breached it's restart limit of {self.max_restarts} "
                                    "and will no longer try to be restarted."
                                )
                                self.processes.pop(id)
                                self.connections.pop(id)
                await asyncio.sleep(self.sleep)
            except Exception:
                logger.exception(f"Caught exception trying to poll camera connections.")
