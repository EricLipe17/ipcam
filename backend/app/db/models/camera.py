from sqlmodel import Field, Relationship, SQLModel


class StreamBase(SQLModel):
    camera_id: int = Field(foreign_key="camera.id", ondelete="CASCADE", index=True)
    codec: str = Field()
    time_base_num: int = Field()
    time_base_den: int = Field()


class AudioStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    camera: "Camera" = Relationship(back_populates="audio_stream")
    sample_rate: int = Field()
    layout_name: str = Field()
    format_name: str = Field()


class VideoStream(StreamBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    camera: "Camera" = Relationship(back_populates="video_stream")
    height: int = Field()
    width: int = Field()
    sample_aspect_ratio_num: int = Field()
    sample_aspect_ratio_den: int = Field()
    framerate: int = Field()
    gop_size: int = Field()
    pix_fmt: str = Field()


class CameraBase(SQLModel):
    name: str = Field(index=True)
    url: str = Field(description="The RTSP url of the camera.")
    location: str | None = Field(
        default=None, description="The location of the IP camera."
    )

    force_transcode: bool | None = Field(
        default=False,
        description="""Some IP cameras don't compress their streams. If that is the case, this flag tells the AV
        pipeline to transcode the stream so that it is compressed.""",
    )


class Camera(CameraBase, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    active_playlist: str | None = Field(
        default=None, description="The live HLS playlist of the IP camera."
    )
    segment_length: int = Field(default=2)
    is_recording: bool = Field(default=False)

    # TODO: Should we store all available audio/video streams from the camera?
    audio_stream: AudioStream | None = Relationship(
        back_populates="camera", cascade_delete=True
    )
    video_stream: VideoStream | None = Relationship(
        back_populates="camera", cascade_delete=True
    )


class CameraCreate(CameraBase):
    pass
