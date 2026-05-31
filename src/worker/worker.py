import asyncio
import inspect
import logging
import queue
import time
import uuid
from functools import partial
from multiprocessing import Process, Queue
from typing import Optional, Union

from betsys import (
    DriverCode,
    PostgresDBConfig,
    LiteDBConfig,
    DriverConfig,
    SportEventDriver,
    DBContext,
    CheckPoint,
    MatchDetails,
    Signal
)

from src.worker.code import StatusCode, SignalMethodCode
from src.worker.handler import QueueHandler
from src.worker.tuple import WorkerResponse, SignalResponse, LogEntry, ProgressResponse

_logger = logging.getLogger(__name__)


class WorkerDriverProcess(object):
    """
    Управление процессом.
    """
    def __init__(
            self,
            driver_code: DriverCode,
            db_config: Union[PostgresDBConfig, LiteDBConfig],
            driver_config: DriverConfig,
            maxsize: int = 500
    ) -> None:
        self._driver_code = driver_code
        self._db_config = db_config
        self._driver_config = driver_config

        # Очереди для общения
        self.commands_queue = Queue(maxsize=maxsize)
        self.resources_queue = Queue(maxsize=maxsize)
        self.logging_queue = Queue(maxsize=maxsize)
        self.signals_queue = Queue(maxsize=maxsize)
        self.progress_queue = Queue(maxsize=maxsize)

        self._process = Process(
            target=self._run,
            args=(
                self.commands_queue,
                self.resources_queue,
                self.logging_queue,
                self.signals_queue,
                self.progress_queue
            )
        )

        self._driver: Optional[SportEventDriver] = None

    @property
    def process(self) -> Process:
        return self._process

    @property
    def driver_code(self) -> DriverCode:
        return self._driver_code

    def _run(
            self,
            commands_queue: Queue,
            resources_queue: Queue,
            logging_queue: Queue,
            signal_queue: Queue,
            progress_queue: Queue
    ) -> None:
        """Точка входа для процесса"""
        try:
            handler = QueueHandler(logging_queue)
            logging.getLogger().addHandler(handler)
            logging.getLogger().setLevel(logging.DEBUG)

            # 1. Создаём event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            db_context = DBContext(self._db_config)

            # 2. Создаём экземпляр driver
            self._driver = SportEventDriver(self._driver_code, db_context, self._driver_config)
            self._driver.signal_created.connect(
                partial(self._connected_signal, signal_queue, SignalMethodCode.CREATED),
                weak=False
            )
            self._driver.signal_restored.connect(
                partial(self._connected_signal, signal_queue, SignalMethodCode.RESTORED),
                weak=False)
            self._driver.signal_deleted.connect(
                partial(self._connected_signal, signal_queue, SignalMethodCode.DELETED),
                weak=False)
            self._driver.signal_evaluated.connect(
                partial(self._connected_signal, signal_queue, SignalMethodCode.EVALUATED),
                weak=False)
            self._driver.update_progress.connect(partial(self._connected_progress, progress_queue), weak=False)

            loop.create_task(self._command_listener(commands_queue, resources_queue))

            loop.run_forever()

        except Exception as exception:
            _logger.exception(exception)

    @staticmethod
    async def _connected_signal(
            signal_queue: Queue,
            signal_method_code: SignalMethodCode,
            sender: str,
            signal: Signal,
            match_details: MatchDetails,
            driver_code: DriverCode
    ) -> None:
        signal_queue.put(
            SignalResponse(
                sender=sender,
                signal_method_code=signal_method_code,
                signal=signal,
                match_details=match_details,
                driver_code=driver_code
            )
        )

    @staticmethod
    async def _connected_progress(
            progress_queue: Queue,
            sender: str,
            value: int,
            max_value: int,
            driver_code: DriverCode
    ) -> None:
        progress_queue.put(
            ProgressResponse(
                sender=sender,
                value=value,
                max_value=max_value,
                driver_code=driver_code
            )
        )

    async def _command_listener(self, commands_queue: Queue, resources_queue: Queue) -> None:
        """
        Слушает и обрабатывает команды.
        """
        while True:
            if not commands_queue.empty():
                worker_response: WorkerResponse = commands_queue.get()
                try:

                    if worker_response.target == SportEventDriver.__name__:
                        obj = self._driver
                    elif worker_response.target == CheckPoint.__name__:
                        obj = self._driver.checkpoint
                    elif worker_response.target == DBContext.__name__:
                        obj = self._driver.db_context
                    else:
                        worker_response.status = StatusCode.ERROR
                        resources_queue.put(worker_response)
                        continue

                    attr = getattr(obj, worker_response.method)

                    if isinstance(getattr(type(obj), worker_response.method, None), property):
                        worker_response.result = attr
                    elif inspect.iscoroutinefunction(attr):
                        worker_response.result = await attr(*worker_response.args, **worker_response.kwargs)
                    elif callable(attr):
                        worker_response.result = attr(*worker_response.args, **worker_response.kwargs)
                    else:
                        worker_response.result = attr

                    worker_response.status = StatusCode.SUCCESS

                    resources_queue.put(worker_response)
                except Exception as exception:
                    _logger.exception(exception)
                    worker_response.status = StatusCode.ERROR
                    resources_queue.put(worker_response)

            await asyncio.sleep(0.05)

    def call_method(self, target_name: str, method_name: str, *args, **kwargs):
        """
        Вызвать метод.
        """
        call_id = uuid.uuid4()

        self.commands_queue.put(
            WorkerResponse(
                call_id=call_id,
                target=target_name,
                method=method_name,
                args=args,
                kwargs=kwargs
            )
        )

        return call_id

    def start(self):
        """
        Начать процесс.
        """
        self._process.start()

    def shutdown(self) -> None:
        """
        Завершить процесс.
        """

        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
            self.process.close()

    def get_logs(self) -> list[LogEntry]:
        logs = []
        try:
            while True:
                logs.append(self.logging_queue.get_nowait())
        except queue.Empty:
            pass
        return logs

    def get_signals(self) -> list[SignalResponse]:
        signals = []
        try:
            while True:
                signals.append(self.signals_queue.get_nowait())
        except queue.Empty:
            pass
        return signals

    def get_response(self, call_id: uuid.UUID) -> Optional[WorkerResponse]:
        while True:
            try:
                response = self.resources_queue.get_nowait()
                if response:
                    if response.call_id == call_id:
                        return response
                    else:
                        self.resources_queue.put(response)

            except queue.Empty:
                time.sleep(0.15)

    def get_progress(self) -> list[ProgressResponse]:
        progresses = []
        try:
            while True:
                progresses.append(self.progress_queue.get_nowait())
        except queue.Empty:
            pass
        return progresses
