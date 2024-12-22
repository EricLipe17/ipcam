import asyncio
import multiprocessing as mp
from multiprocessing.connection import Connection

from app.db import get_session
from app.db.models import Camera
from app.processes import CameraProcess
from app.settings.local import settings

if mp.get_start_method() != "spawn":
    print(f"\nForcing multiprocessing to spawn instead of {mp.get_start_method()}.\n")
    mp.set_start_method("spawn", force=True)


class CameraProcessManager:
    def __init__(self):
        self.processes = dict()
        self.connections = dict()
        self.wait_for = 0.1

    def add_camera(self, id: int, name: str, url: str):
        p = None
        try:
            if id in self.processes:
                return f"Cannot create process with name: {name} because it already exists!"
            print(f"adding new camera with id: {id}")

            parent_conn, child_conn = mp.Pipe()

            p = CameraProcess(
                name=name, id=id, url=url, connection=child_conn, daemon=True
            )
            p.start()
            self.processes[id] = p
            self.connections[id] = parent_conn
            return None
        except Exception as e:
            if p and p.is_alive():
                p.kill()
            print(e)
            return f"Caught exception trying to start the recording: {e}"

    async def poll_cameras(self):
        print("Inside poll_cameras")
        log = open("record.log", "a")
        while True:
            for camera, connection in self.connections.items():
                if connection.poll():
                    obj = connection.recv()
                    print(f"Printing to console: {obj}")
                    log.write(f"Received message from {camera}. ")
                    log.write(f"{obj}\n")
                    log.flush()
            await asyncio.sleep(self.wait_for)
