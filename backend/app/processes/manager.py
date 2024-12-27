import asyncio
import logging
import multiprocessing as mp
from multiprocessing.connection import Connection
from typing import List, Dict

from app.processes import CameraProcess
from app.processes.enums import MessageType, ProcessType

logger = logging.getLogger(__name__)

if mp.get_start_method() != "spawn":
    logger.warning(
        f"\nForcing multiprocessing to spawn instead of {mp.get_start_method()}.\n"
    )
    mp.set_start_method("spawn", force=True)


class CameraProcessManager:
    processes: Dict[int, mp.Process]
    connections: Dict[int, Connection]
    restarts = List[mp.Process]
    sleep: float

    def __init__(self):
        self.processes = dict()
        self.connections = dict()
        self.restarts = list()
        self.sleep = 0.5

    def add_camera(self, id: int, name: str, url: str):
        try:
            if id in self.processes:
                return f"Cannot create process with id:{id} because it already exists!"
            logger.info(f"Adding new camera with id:{id}.")

            parent_conn, child_conn = mp.Pipe()
            camera = CameraProcess(
                name=name, id=id, url=url, connection=child_conn, daemon=True
            )
            camera.start()
        except Exception:
            if camera and camera.is_alive():
                logger.warning(
                    f"Camera recording process for id:{id} was alive but killing it due to unknown exception."
                )
                camera.kill()
            msg = f"Caught exception trying to start the recording."
            logger.exception(msg)
            return msg
        else:
            self.processes[id] = camera
            self.connections[id] = parent_conn
            return None

    def copy_process(self, dead_proc, new_conn):
        match dead_proc.proc_type:
            case ProcessType.Camera:
                new_camera = CameraProcess(
                    url=dead_proc.url,
                    id=dead_proc.id,
                    connection=new_conn,
                    daemon=True,
                )
                return new_camera
            case _:
                logger.error(
                    "Received an unknown ProcessType to copy. No copy occurred."
                )
                return None

    async def poll_restart_processes(self):
        while True:
            for id in self.restarts:
                try:
                    dead_proc = self.processes.pop(id)
                    self.connections.pop(id)

                    parent_conn, child_conn = mp.Pipe()
                    new_proc = self.copy_process(dead_proc, child_conn)
                    new_proc.start()
                except Exception:
                    logger.exception(
                        f"Fatal error: Unable to restart process with ID:{id}."
                    )
                    if new_proc and new_proc.is_alive():
                        new_proc.kill()
                else:
                    self.processes[new_proc.id] = new_proc
                    self.connections[new_proc.id] = parent_conn

            await asyncio.sleep(self.sleep)

    async def poll_cameras(self):
        while True:
            try:
                for id, connection in self.connections.items():
                    if connection.poll():
                        message = connection.recv()
                        message.handle()
                        if message.m_type == MessageType.Error:
                            ## TODO: if a camera fails should we restart it?
                            self.restarts.append(id)
                            logger.warning(f"Encountered error with Camera:{id}.")
                await asyncio.sleep(self.sleep)
            except Exception:
                logger.exception(
                    f"Caught exception trying to poll camera connections for id:{id}."
                )
