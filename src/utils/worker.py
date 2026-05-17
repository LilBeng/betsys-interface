import logging
from typing import Callable, Optional

from PySide6.QtCore import Signal, QObject, QThread

_logger = logging.getLogger(__name__)


class Worker(QObject):
    started = Signal()
    _finished = Signal(object)

    def __init__(self, thread: QThread) -> None:
        super().__init__()
        self._thread = thread

        self._func = None
        self._args = None
        self._kwargs = None
        self._callback = None

        self.is_running = False

        self.moveToThread(self._thread)
        self._thread.started.connect(self._run)

    def start(self, callback: Optional[Callable], func: Callable, *args, **kwargs) -> None:
        self._callback = callback
        self._func = func
        self._args = args if args else ()
        self._kwargs = kwargs if kwargs else {}

        if callback:
            self._finished.connect(callback)

        self._thread.start()

    def _run(self) -> None:
        try:
            self.is_running = True

            self.started.emit()
            result = self._func(*self._args, **self._kwargs)
            self._finished.emit(result)
        except Exception as exception:
            _logger.exception(exception)
        finally:
            if self._callback:
                self._finished.disconnect()

            self._func = None
            self._args = None
            self._kwargs = None
            self._callback = None

            self.is_running = False

            self._thread.quit()
