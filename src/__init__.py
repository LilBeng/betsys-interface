import os

_DIR = "configs"

AUTOSAVE_DIR = "autosave"

DISPLAY = os.path.join(_DIR, "display.ini")
CONFIG = os.path.join(_DIR, "config.cfg")
DRIVER = os.path.join(_DIR, "driver.cfg")
ERRORS = os.path.join(_DIR, "errors.log")

os.makedirs(_DIR, exist_ok=True)
