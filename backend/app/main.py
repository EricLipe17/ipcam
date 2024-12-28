from app import process_manager
from app.routers import auth, cameras, users
from app.settings.local import settings

import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from typing import Any
import uvicorn


logging.basicConfig(
    level=logging.INFO,
)


class EndpointFilter(logging.Filter):
    def __init__(
        self,
        path: str,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find(self._path) == -1


# Filter out uvicorn logs coming from the segments and playlist endpoints
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(EndpointFilter(path="/segments"))
uvicorn_logger.addFilter(EndpointFilter(path="/output.m3u8"))

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Executing startup tasks.")
    process_manager.start_processes()
    asyncio.create_task(process_manager._poll_processes())
    asyncio.create_task(process_manager._poll_restarts())
    yield
    logger.info("Executing shutdown tasks")


app = FastAPI(
    root_path=settings.path_prefix,
    lifespan=lifespan,
    title="Backend API",
    description="The description of the API",
    summary="The summmary of the API",
    version=settings.version,
    terms_of_service="http://example.com/terms/",
    contact={},
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(users.router)


@app.get("/")
async def main():
    print("Inside of main!")
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, lifespan="on")
