from betsys import LangCode

from src.utils.decorators import singleton


@singleton
class AppLang(object):
    code = LangCode.RU
