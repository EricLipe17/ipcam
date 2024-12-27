from dataclasses import dataclass
import logging

from app.processes.enums import MessageType


logger = logging.getLogger(__name__)


@dataclass
class Message:
    process_id: int
    process_name: str
    m_type: MessageType = MessageType.Log
    message: str = ""
    level: int = logging.INFO

    def handle(self):
        logger.log(
            level=self.level,
            msg=f"{self.process_name}:{self.process_id}  --  {self.message}",
        )
