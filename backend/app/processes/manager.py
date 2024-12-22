import asyncio
import logging
import multiprocessing as mp
from multiprocessing.connection import Connection
from typing import Dict

from app.processes import CameraProcess, MessageType

logger = logging.getLogger(__name__)

if mp.get_start_method() != "spawn":
    logger.warning(
        f"\nForcing multiprocessing to spawn instead of {mp.get_start_method()}.\n"
    )
    mp.set_start_method("spawn", force=True)


class CameraProcessManager:
    processes: Dict[int, mp.Process]
    connections: Dict[int, Connection]
    wait_for: float

    def __init__(self):
        self.processes = dict()
        self.connections = dict()
        self.wait_for = 0.5

    def add_camera(self, id: int, name: str, url: str):
        camera, parent_conn, child_conn = None, None, None
        try:
            if id in self.processes:
                return f"Cannot create process with id:{id} because it already exists!"
            logger.info(f"Adding new camera with id:{id}.")

            parent_conn, child_conn = mp.Pipe()
            camera = CameraProcess(
                name=name, id=id, url=url, connection=child_conn, daemon=True
            )
            camera.start()
            self.processes[id] = camera
            self.connections[id] = parent_conn
            return None
        except Exception:
            if camera and camera.is_alive():
                logger.warning(
                    f"Camera recording process for id:{id} was alive but killing it due to unknown exception."
                )
                camera.kill()
            self.processes.pop(id, None)
            self.connections.pop(id, None)
            msg = f"Caught exception trying to start the recording."
            logger.exception(msg)
            return msg

    async def poll_cameras(self):
        while True:
            try:
                for id, connection in self.connections.items():
                    if connection.poll():
                        message = connection.recv()
                        message.handle()
                        if message.m_type is MessageType.Error:
                            ## TODO: if a camera fails should we restart it?
                            pass
                await asyncio.sleep(self.wait_for)
            except Exception:
                logger.exception(
                    f"Caught exception trying to poll camera connections for id:{id}."
                )
