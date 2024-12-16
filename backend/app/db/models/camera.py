from sqlmodel import Field, Relationship, SQLModel


class StreamBase(SQLModel):
    camera_id: int | None = Field(
        default=None, foreign_key="camera.id", ondelete="CASCADE"
    )
    codec: str
    time_base_num: int
    time_base_den: int


class AudioStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sample_rate: int
    layout_name: str
    format_name: str


class VideoStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    height: int
    width: int
    sample_aspect_ratio_num: int
    sample_aspect_ratio_den: int
    framerate_num: int
    framerate_den: int
    gop_size: int
    pix_fmt: str


class CameraBase(SQLModel):
    name: str
    url: str
    location: str | None = None


class Camera(CameraBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    active_playlist: str
    segment_length: int = 10
    is_recording: bool = False


class CameraCreate(CameraBase):
    pass


class CameraPublic(Camera):
    pass
