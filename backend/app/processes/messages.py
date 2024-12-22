from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    Log = 1
    Error = 2


@dataclass
class Message:
    type: MessageType
    message: str
