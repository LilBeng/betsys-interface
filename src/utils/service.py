import logging
from datetime import date
from typing import Optional, Callable

from PySide6.QtCore import QObject, QStandardPaths, Signal as pysideSignal, QTimer, Slot, QThread
from PySide6.QtWidgets import QFileDialog, QMessageBox, QDialog
from betsys import (
    SportEventDriver,
    DBContext,
    MultiDriverConfig,
    DriverCode,
    RunState,
    CheckPoint,
    Signal,
    get_driver_name,
    MatchDetails,
    MatchCode
)
from betsys.driver.base import Information
from qasync import asyncSlot

from src import CONFIG, DRIVER
from src.dialogs.config import DAOConfigDialog, DriverConfigDialog
from src.dialogs.date import DatePickerDialog
from src.dialogs.league import LeagueDAODialog
from src.dialogs.match import MatchDetailsDAODialog
from src.dialogs.prompt import PromptDAODialog
from src.dialogs.script import ScriptDAODialog
from src.dialogs.signal import SignalDAODialog
from src.dialogs.transfer import TransferDialog
from src.utils.cache import DataCache
from src.utils.lang import AppLang
from src.utils.worker import Worker
from src.worker.code import StatusCode, SignalMethodCode
from src.worker.tuple import WorkerResponse
from src.worker.worker import WorkerDriverProcess

_logger = logging.getLogger(__name__)


class SportEventService(QObject):
    """
    Сервис спортивных событий.
    """
    status_message = pysideSignal(str)

    signal_created = pysideSignal(Signal, MatchDetails, DriverCode)
    signal_evaluated = pysideSignal(Signal, MatchDetails, DriverCode)
    signal_deleted = pysideSignal(Signal, MatchDetails, DriverCode)
    signal_restored = pysideSignal(Signal, MatchDetails, DriverCode)

    update_progress = pysideSignal(int, int, DriverCode)

    def __init__(
            self,
            db_context: DBContext,
            multi_driver_config: MultiDriverConfig,
            *args,
            **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.db_context = db_context
        self.multi_driver_config = multi_driver_config
        self.workers: dict[DriverCode, WorkerDriverProcess] = {}

        self._timer = QTimer()
        self._timer.timeout.connect(self._fetch_worker)
        self._timer.start(300)

        self._thread = QThread()
        self._worker = Worker(self._thread)

    @staticmethod
    def get_name(cls: object, prop: callable) -> Optional[str]:
        for name, attr in cls.__dict__.items():
            if attr is prop:
                return name
        return None

    def _get_response(
            self,
            worker: WorkerDriverProcess,
            target_name: str,
            method_name: str,
            *args,
            **kwargs
    ) -> Optional[WorkerResponse]:
        self.update_progress.emit(-1, -1, None)

        call_id = worker.call_method(target_name, method_name, *args, **kwargs)

        response = worker.get_response(call_id)

        self.update_progress.emit(1, 1, None)
        if response and response.status == StatusCode.SUCCESS:
            return response

        if not response:
            _logger.error(f"Response not found")
            return None
        elif response.status == StatusCode.ERROR:
            _logger.error(f"Response error: {response.error}")
            return None

    def _fetch_worker(self) -> None:
        for worker in self.workers.values():
            entry_logs = worker.get_logs()
            for entry in entry_logs:
                if entry.level_no >= logging.getLogger().getEffectiveLevel():
                    _logger.handle(
                        logging.LogRecord(
                            name=entry.name,
                            level=entry.level_no,
                            pathname=entry.filename,
                            lineno=entry.line_no,
                            msg=entry.msg,
                            args=(),
                            exc_info=None
                        ))

            signal_responses = worker.get_signals()
            for response in signal_responses:
                _logger.info(
                    f"Sender {response.sender} - get signal "
                    f"(signal_id={response.signal.signal_id}, driver_code={response.driver_code})"
                )

                if response.signal_method_code == SignalMethodCode.CREATED:
                    self.signal_created.emit(response.signal, response.match_details, response.driver_code)
                elif response.signal_method_code == SignalMethodCode.DELETED:
                    self.signal_deleted.emit(response.signal, response.match_details, response.driver_code)
                elif response.signal_method_code == SignalMethodCode.RESTORED:
                    self.signal_restored.emit(response.signal, response.match_details, response.driver_code)
                elif response.signal_method_code == SignalMethodCode.EVALUATED:
                    self.signal_evaluated.emit(response.signal, response.match_details, response.driver_code)

            progress_responses = worker.get_progress()
            for response in progress_responses:
                self.update_progress.emit(response.value, response.max_value, response.driver_code)

            del entry_logs
            del signal_responses
            del progress_responses

    def _check_driver(self, driver_code: DriverCode, is_running: bool = True) -> bool:
        worker = self.workers.get(driver_code)
        if worker:
            response = self._get_response(
                worker,
                SportEventDriver.__name__,
                self.get_name(SportEventDriver, SportEventDriver.state)
            )
            if is_running:
                condition = response.result == RunState.RUNNING
            else:
                condition = response.result != RunState.RUNNING

            if response and condition:
                if is_running:
                    self.status_message.emit(
                        self.tr("Для выполнения действия остановите драйвер «{}»").format(
                            get_driver_name(driver_code, AppLang.code)
                        )
                    )
                else:
                    self.status_message.emit(
                        self.tr("Для выполнения действия запустите драйвер «{}»").format(
                            get_driver_name(driver_code, AppLang.code)
                        )
                    )
                return False

        return True

    def _start_thread(self, callback: Optional[Callable], func: Callable, *args) -> None:
        if not self._worker.is_running:
            self._worker.start(callback, func, *args)
        else:
            self.status_message.emit(self.tr("Дождитесь завершения предыдущего действия"))

    def _remove_signal(self, signal_id: str, driver_code: DriverCode) -> None:
        """
        Удалить сигнал.

        :param signal_id: Идентификатор сигнала.
        :param driver_code: Код драйвера.
        """
        worker = self.workers.get(driver_code)
        if worker:
            response = self._get_response(
                worker,
                CheckPoint.__name__,
                CheckPoint.remove_signal.__name__,
                signal_id
            )
            if response:
                _logger.info(f"Signal (signal id={signal_id}, driver code={driver_code}) deleted")
            else:
                _logger.info(f"Signal (signal id={signal_id}, driver code={driver_code}) not deleted")
        else:
            _logger.info(f"Signal (signal id={signal_id}, driver code={driver_code}) not deleted")

    @Slot()
    def _run(self, result: tuple[bool, DriverCode, bool]) -> None:
        """
        Запустить драйвер.
        """
        flag, driver_code, is_checkpoint = result
        if flag:
            worker = self.workers.get(driver_code)

            if is_checkpoint:
                file_path, _ = QFileDialog.getOpenFileName(
                    self.parent(),
                    self.tr("Выбор файла"),
                    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
                    self.tr("Файлы контрольной точки (*.cp)")
                )

                if file_path:
                    self.update_progress.emit(-1, -1, driver_code)

                    try:
                        checkpoint = CheckPoint.load(file_path)
                    except Exception as exception:
                        _logger.exception(exception)
                        QMessageBox.critical(self.parent(), self.tr("Запуск"), self.tr("Не удалось открыть файл"))
                        return None

                    self.update_progress.emit(1, 1, driver_code)

                    self.status_message.emit(
                        self.tr("Драйвер «{}» начинает работу").format(get_driver_name(driver_code, AppLang.code))
                    )
                    worker.call_method(
                        SportEventDriver.__name__,
                        SportEventDriver.run_with_checkpoint.__name__,
                        checkpoint
                    )

                else:
                    _logger.warning(f"Driver (code={driver_code}) not running")

            else:
                q_date = DatePickerDialog.get_date(parent=self.parent())
                if q_date:
                    started_date = date(q_date.year(), q_date.month(), q_date.day())

                    self.status_message.emit(
                        self.tr("Драйвер «{}» начинает работу").format(get_driver_name(driver_code, AppLang.code))
                    )

                    worker.call_method(SportEventDriver.__name__, SportEventDriver.run.__name__, started_date)
                else:
                    _logger.warning(f"Driver (code={driver_code}) not running")

    @Slot()
    def _stop(self, result: tuple[bool, DriverCode, bool]) -> None:
        """
        Остановить драйвер.
        """
        flag, driver_code, is_checkpoint = result

        if flag:
            worker = self.workers.get(driver_code)
            if is_checkpoint:
                file_path, _ = QFileDialog.getSaveFileName(
                    self.parent(),
                    self.tr("Сохранить файл"),
                    QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
                    self.tr("Файлы контрольной точки (*.cp)")
                )

                if file_path:
                    try:
                        response = self._get_response(
                            worker,
                            SportEventDriver.__name__,
                            SportEventDriver.stop.__name__,
                            True
                        )
                        if response:
                            self.update_progress.emit(-1, -1, driver_code)

                            response.result.save(file_path)

                            self.update_progress.emit(1, 1, driver_code)

                            self.status_message.emit(
                                self.tr("Драйвер «{}» остановлен").format(get_driver_name(
                                    driver_code,
                                    AppLang.code)
                                )
                            )
                        else:
                            self.status_message.emit(self.tr("Не удалось получить данные"))

                        del response
                    except Exception as exception:
                        _logger.exception(exception)

                        self.update_progress.emit(1, 1, driver_code)

                        QMessageBox.critical(
                            self.parent(),
                            self.tr("Остановка"),
                            self.tr("Не удалось сохранить файл")
                        )
                else:
                    _logger.warning(f"Driver (code={driver_code}) not stopped")

            else:
                worker.call_method(
                    SportEventDriver.__name__,
                    SportEventDriver.stop.__name__,
                )

                self.status_message.emit(
                    self.tr("Драйвер «{}» остановлен").format(get_driver_name(driver_code, AppLang.code))
                )

        else:
            _logger.warning(f"Driver (code={driver_code}) not found")
            self.status_message.emit(
                self.tr("Драйвер «{}» не работает").format(get_driver_name(driver_code, AppLang.code))
            )

    @Slot()
    def _update_data(self, driver_code: DriverCode, is_script: bool) -> None:
        """
        Обновить сценарии.

        :param driver_code: Код драйвера.
        :param is_script: Флаг.
        """
        worker = self.workers.get(driver_code)
        if worker:
            response = self._get_response(
                worker,
                SportEventDriver.__name__,
                self.get_name(SportEventDriver, SportEventDriver.state)
            )
            if response and response.result == RunState.RUNNING:
                if is_script:
                    response_update = self._get_response(
                        worker,
                        SportEventDriver.__name__,
                        SportEventDriver.update_scripts.__name__
                    )

                else:
                    response_update = self._get_response(
                        worker,
                        SportEventDriver.__name__,
                        SportEventDriver.update_leagues.__name__
                    )

                if response_update and response_update.result:
                    self.status_message.emit(self.tr("Данные обновлены"))
                else:
                    self.status_message.emit(self.tr("Не удалось обновить данные"))
            elif not response:
                self.status_message.emit(self.tr("Не удалось получить данные"))
            else:
                self.status_message.emit(
                    self.tr("Для выполнения действия запустите драйвер «{}»").format(
                        get_driver_name(driver_code, AppLang.code)
                    )
                )
        else:
            self.status_message.emit(
                self.tr("Драйвер «{}» не инициализирован").format(get_driver_name(driver_code, AppLang.code))
            )

    @asyncSlot()
    async def _download_leagues(self, result: tuple[bool, DriverCode]) -> None:
        """
        Скачать лиги.
        """
        flag, driver_code = result
        if flag:
            if driver_code == DriverCode.FOOTBALL:
                match_code = MatchCode.FOOTBALL
            elif driver_code == DriverCode.HOCKEY:
                match_code = MatchCode.HOCKEY
            elif driver_code == DriverCode.VOLLEYBALL:
                match_code = MatchCode.VOLLEYBALL
            else:
                self.status_message.emit(self.tr("Не удалось получить данные"))
                return None

            config = self.multi_driver_config.config.get(driver_code)
            if config:
                try:
                    flag = await SportEventDriver.download_leagues(
                        self.db_context,
                        match_code,
                        config.scraper_config,
                        config.lang_code
                    )
                    if flag:
                        DataCache.leagues.clear()
                        self.status_message.emit(self.tr("Лиги загружены"))
                    else:
                        QMessageBox.critical(
                            self.parent(),
                            self.tr("Загрузка лиг"),
                            self.tr("Не удалось загрузить данные")
                        )
                except Exception as exception:
                    _logger.exception(exception)
                    QMessageBox.critical(
                        self.parent(),
                        self.tr("Загрузка лиг"),
                        self.tr("Не удалось загрузить данные")
                    )

            else:
                QMessageBox.critical(
                    self.parent(),
                    self.tr("Загрузка лиг"),
                    self.tr("Не найдена конфигурация драйвера «{}»").format(
                        get_driver_name(driver_code, AppLang.code)
                    )
                )

    @Slot()
    def _edit_driver_config(self, result: tuple[bool, DriverCode]) -> None:
        """
        Редактировать конфигурацию драйвера.
        """
        flag, driver_code = result
        if flag:
            config = self.multi_driver_config.config.get(driver_code)
            if config:
                dialog = DriverConfigDialog(config, parent=self.parent())
            else:
                dialog = DriverConfigDialog(parent=self.parent())

            if dialog.exec() == QDialog.DialogCode.Accepted:
                config = dialog.config

                self.multi_driver_config.config[driver_code] = config
                try:
                    self.multi_driver_config.save(DRIVER)

                    _logger.info("File driver config saved")

                    worker = self.workers.get(driver_code)
                    if worker:
                        self._get_response(
                            worker,
                            SportEventDriver.__name__,
                            SportEventDriver.update_config.__name__,
                            config
                        )

                    self.status_message.emit(self.tr("Конфигурация сохранена"))
                except Exception as exception:
                    _logger.exception(exception)

                    self.status_message.emit(self.tr("Не удалось сохранить конфигурацию"))

    @asyncSlot()
    async def _edit_dao_config(self, flag: bool) -> None:
        """
        Редактировать конфигурацию БД.
        """
        if flag:
            dialog = DAOConfigDialog(self.db_context.config, parent=self.parent())
            if dialog.exec() == QDialog.DialogCode.Accepted:
                config = dialog.config
                try:
                    await self.db_context.reconnect(config)

                    config.save(CONFIG)

                    _logger.info("File DAO config updated")

                    for driver_code, worker in self.workers.items():
                        response = self._get_response(
                            worker,
                            DBContext.__name__,
                            DBContext.reconnect.__name__,
                            config
                        )

                        if response:
                            _logger.info(f"Driver (driver code={driver_code}) DAO config updated")
                        else:
                            _logger.warning(f"Driver (driver code={driver_code}) DAO config not updated")

                    self.status_message.emit(self.tr("Конфигурация БД обновлена"))
                except Exception as exception:
                    _logger.exception(exception)

                    self.status_message.emit(self.tr("Не удалось обновить конфигурацию БД"))

    def shutdown_workers(self) -> None:
        """
        Остановить процессы.
        """
        for worker in self.workers.values():
            worker.shutdown()

    @Slot()
    def get_object(
            self,
            callback: Optional[callable],
            driver_code: DriverCode,
            target_name: str,
            method_name: str,
            *args,
            **kwargs
    ) -> None:
        def check() -> Optional[Information]:
            if self._check_driver(driver_code, False):
                worker = self.workers.get(driver_code)
                if worker:
                    response = self._get_response(worker, target_name, method_name, *args, **kwargs)
                    if response and response.status == StatusCode.SUCCESS:
                        return response.result
                    else:
                        self.status_message.emit(self.tr("Не удалось получить данные"))
                else:
                    self.status_message.emit(
                        self.tr("Драйвер «{}» не инициализирован").format(get_driver_name(driver_code, AppLang.code))
                    )

            return None

        self._start_thread(callback, check)

    def save_checkpoint(self, file_path: str, driver_code: DriverCode) -> None:
        def _save(checkpoint: CheckPoint) -> None:
            if checkpoint:
                self.update_progress.emit(-1, -1, driver_code)
                try:
                    checkpoint.save(file_path)

                    self.status_message.emit(self.tr("Контрольная точка сохранена"))
                except Exception as exception:
                    _logger.exception(exception)
                    QMessageBox.critical(
                        self.parent(),
                        self.tr("Сохранение файла"),
                        self.tr("Не удалось сохранить файл")
                    )

                self.update_progress.emit(1, 1, driver_code)
            else:
                self.status_message.emit(
                    self.tr("Для выполнения действия запустите драйвер «{}»").format(
                        get_driver_name(driver_code, AppLang.code)
                    )
                )

        self.get_object(
            _save,
            driver_code,
            SportEventDriver.__name__,
            self.get_name(SportEventDriver, SportEventDriver.checkpoint)
        )

    def remove_signal(self, signal_id: str, driver_code: DriverCode) -> None:
        self._start_thread(None, self._remove_signal, signal_id, driver_code)

    def fing_signal_ids(self, callback: Callable) -> None:
        """
        Получить идентификаторы всех сигналов.

        :return: Список идентификаторов.
        """
        def get_signals() -> list[str]:
            signals_id = []
            for worker in self.workers.values():
                response = self._get_response(
                    worker,
                    CheckPoint.__name__,
                    "signals"
                )
                if response and response.result:
                    for signal_id in response.result:
                        signals_id.append(signal_id)

            return signals_id

        self._start_thread(callback, get_signals)

    @Slot()
    def run(self, driver_code: DriverCode, is_checkpoint: bool) -> None:
        config = self.multi_driver_config.config.get(driver_code)
        if not config:
            _logger.warning(f"Driver (code={driver_code}) config not found")
            self.status_message.emit(
                self.tr("Не найдена конфигурация драйвера «{}»").format(
                    get_driver_name(driver_code, AppLang.code)
                )
            )
            return None

        worker = WorkerDriverProcess(driver_code, self.db_context.config, config)

        self.workers[driver_code] = worker

        worker.start()

        self.status_message.emit(
            self.tr("Драйвер «{}» инициализирован").format(get_driver_name(driver_code, AppLang.code))
        )

        self._run((True, driver_code, is_checkpoint))

    @Slot()
    def stop(self, driver_code: DriverCode, is_checkpoint: bool) -> None:
        def check() -> tuple[bool, DriverCode, bool]:
            return self._check_driver(driver_code, False), driver_code, is_checkpoint

        worker = self.workers.get(driver_code)
        if worker:
            self._start_thread(self._stop, check)
        else:
            _logger.warning(f"Driver (code={driver_code}) not found")
            self.status_message.emit(
                self.tr("Драйвер «{}» не инициализирован").format(get_driver_name(driver_code, AppLang.code))
            )

    @Slot()
    def update_data(self, driver_code: DriverCode, is_script: bool) -> None:
        self._start_thread(None, self._update_data, driver_code, is_script)

    @Slot()
    def download_leagues(self, driver_code: DriverCode) -> None:
        def check() -> tuple[bool, DriverCode]:
            return self._check_driver(driver_code), driver_code

        self._start_thread(self._download_leagues, check)

    @Slot()
    def edit_driver_config(self, driver_code: DriverCode) -> None:
        def check() -> tuple[bool, DriverCode]:
            return self._check_driver(driver_code), driver_code

        self._start_thread(self._edit_driver_config, check)

    @Slot()
    def edit_dao_config(self):
        def check() -> bool:
            for driver_code in self.workers:
                flag = self._check_driver(driver_code)
                if not flag:
                    return False

            return True

        self._start_thread(self._edit_dao_config, check)

    @Slot()
    def show_transfer_dao(self) -> None:
        dialog = TransferDialog(self.db_context)
        dialog.exec()

    @Slot()
    def show_leagues_dialog(self) -> None:
        dialog = LeagueDAODialog(self.db_context)
        dialog.exec()

    @Slot()
    def show_matches_dialog(self) -> None:
        dialog = MatchDetailsDAODialog(self.db_context)
        dialog.exec()

    @Slot()
    def show_scripts_dialog(self) -> None:
        dialog = ScriptDAODialog(self.db_context)
        dialog.exec()

    @Slot()
    def show_signals_dialog(self) -> None:
        dialog = SignalDAODialog(self.db_context)
        dialog.exec()

    @Slot()
    def show_prompts_dialog(self) -> None:
        dialog = PromptDAODialog(self.db_context)
        dialog.exec()
