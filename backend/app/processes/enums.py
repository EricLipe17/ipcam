from enum import Enum


class MessageType(Enum):
    Log = 1
    Error = 2


class ProcessType(Enum):
    Camera = 1
