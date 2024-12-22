from sqlmodel import Field, Relationship, SQLModel


class StreamBase(SQLModel):
    camera_id: int = Field(foreign_key="camera.id", ondelete="CASCADE", index=True)
    codec: str = Field()
    time_base_num: int = Field()
    time_base_den: int = Field()


class AudioStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    sample_rate: int = Field()
    layout_name: str = Field()
    format_name: str = Field()


class VideoStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    height: int = Field()
    width: int = Field()
    sample_aspect_ratio_num: int = Field()
    sample_aspect_ratio_den: int = Field()
    framerate: int = Field()
    gop_size: int = Field()
    pix_fmt: str = Field()


class CameraBase(SQLModel):
    name: str = Field(index=True)
    url: str = Field()
    location: str | None = Field(default=None)


class Camera(CameraBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    active_playlist: str | None = Field(default=None)
    segment_length: int = Field(default=2)
    is_recording: bool = Field(default=False)


class CameraCreate(CameraBase):
    pass


class CameraPublic(Camera):
    pass
