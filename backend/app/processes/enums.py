from enum import Enum


class MessageType(Enum):
    Log = 1
    Error = 2


class ProcessType(Enum):
    AVCamera = 1
