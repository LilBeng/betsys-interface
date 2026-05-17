import logging
from multiprocessing import Queue

from src.worker.tuple import LogEntry


class QueueHandler(logging.Handler):
    def __init__(self, queue: Queue) -> None:
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        self.queue.put(
            LogEntry(
                name=record.name,
                levelname=record.levelname,
                level_no=record.levelno,
                msg=record.msg,
                filename=record.filename,
                line_no=record.lineno,
                created=record.created
            )
        )
