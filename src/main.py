import asyncio
import os
import traceback
from typing import Optional, Union

from PySide6.QtCore import QTranslator, QLibraryInfo, QFile, QTextStream
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from betsys import LiteDBConfig, DBContext, MultiDriverConfig, PostgresDBConfig, create_tables
from pydantic import ValidationError
from qasync import QEventLoop

import resources_rc  # noqa
from src import DRIVER, CONFIG
from src.dialogs.config import DAOConfigDialog
from src.main_window import MainWindow


def load_db() -> Optional[Union[LiteDBConfig, PostgresDBConfig]]:
    """
    Загрузка конфигурации БД из файла.
    """
    if not os.path.exists(CONFIG):
        return None

    try:
        return LiteDBConfig.load(CONFIG)
    except ValidationError:
        pass

    try:
        return PostgresDBConfig.load(CONFIG)
    except ValidationError:
        pass


def load_multiconfig() -> Optional[MultiDriverConfig]:
    """
    Загрузка конфигурации БД из файла.
    """
    if not os.path.exists(DRIVER):
        return None

    try:
        return MultiDriverConfig.load(DRIVER)
    except ValidationError:
        pass


def check_dao(db_context: DBContext) -> bool:
    try:
        if asyncio.run(db_context.check_connection()):
            asyncio.run(create_tables(db_context.async_engine))

            return True
    except ExceptionGroup:
        return False


def load_style_sheet(filename: str) -> str:
    file = QFile(filename)
    file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
    stream = QTextStream(file)

    return stream.readAll()


def run(only_database: bool = False):
    app = QApplication([])

    font = QFont("Segoe UI", 12)
    app.setFont(font)

    translator = QTranslator()
    translator.load("qt_ru", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    app.installTranslator(translator)

    qt_base_translator = QTranslator()
    qt_base_translator.load("qtbase_ru", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    app.installTranslator(qt_base_translator)

    is_load = False
    while not is_load:
        if db_config := load_db():
            try:
                db_context = DBContext(db_config)

                flag = check_dao(db_context)
                if flag:
                    loop = QEventLoop(app)

                    multi_driver_config = load_multiconfig()
                    if not multi_driver_config:
                        multi_driver_config = MultiDriverConfig(config={})
                        if not only_database:
                            multi_driver_config.save(DRIVER)

                    main_window = MainWindow(db_context, multi_driver_config, only_database)
                    main_window.show()

                    is_load = True

                    with loop:
                        loop.run_forever()
                else:
                    QMessageBox.critical(
                        app.activeModalWidget(),
                        app.tr("Подключение"),
                        app.tr("Не удалось подключиться к базе данных")
                    )

                    dialog = DAOConfigDialog(db_config)
                    if dialog.exec() == QDialog.DialogCode.Rejected:
                        is_load = True

            except Exception as exception:
                traceback.print_exception(exception)
                QMessageBox.critical(
                    app.activeModalWidget(),
                    app.tr("Критическая ошибка"),
                    str(exception)
                )

                is_load = True

        else:
            dialog = DAOConfigDialog()
            if dialog.exec() == QDialog.DialogCode.Rejected:
                is_load = True
