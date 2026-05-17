from enum import Enum


class StatusCode(int, Enum):
    SUCCESS = 0
    ERROR = 1


class SignalMethodCode(int, Enum):
    CREATED = 0
    RESTORED = 1
    DELETED = 2
    EVALUATED = 3
