from dataclasses import dataclass
from enum import Enum
import logging


logger = logging.getLogger(__name__)


class MessageType(Enum):
    Log = 1
    Error = 2


@dataclass
class Message:
    process_id: int
    process_name: str
    m_type: MessageType
    level: int = logging.INFO
    message: str

    def handle(self):
        logger.log(
            level=self.level,
            msg=f"{self.process_name}:{self.process_id}  --  {self.message}",
        )
