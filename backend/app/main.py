from app import camera_manager
from app.routers import auth, cameras, users
from app.settings.local import settings

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Executing startup tasks")
    asyncio.create_task(camera_manager.poll_cameras())
    yield
    print("Executing shutdown tasks")


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
