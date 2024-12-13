from pydantic import BaseModel

class Base(BaseModel):
    id: int

class StreamBase(Base):
    camera_ref: int
    codec: str
    time_base: tuple[int, int]

class AudioSteam(StreamBase):
    sample_rate: int
    layout_name: str
    format_name: str

class VideoStream(StreamBase):
    height: int
    width: int
    sample_aspect_ratio: tuple[int, int]
    # bit_rate: int
    framerate: tuple[int, int]
    gop_size: int
    pix_fmt: str

class CameraIn(BaseModel):
    name: str
    url: str
    location: str | None = None

class Camera(CameraIn, Base):
    active_playlist: str
    video: VideoStream
    audio: AudioSteam | None = None
    segment_length: int = 10
    is_recording: bool = False








class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class FormData(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: set[str] = set()
