import uuid
from dataclasses import dataclass, field
from typing import Optional, Any

from betsys import DriverCode, MatchDetails, Signal

from src.worker.code import StatusCode, SignalMethodCode


@dataclass
class LogEntry:
    """
    Тип логирования.
    """
    name: str
    levelname: str
    level_no: int
    msg: str
    filename: str
    line_no: int
    created: float


@dataclass
class WorkerResponse:
    """
    Тип запроса.
    """
    call_id: uuid.UUID
    target: str
    method: str
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    status: Optional[StatusCode] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class SignalResponse:
    sender: str
    signal_method_code: SignalMethodCode
    signal: Signal
    match_details: MatchDetails
    driver_code: DriverCode


@dataclass
class ProgressResponse:
    sender: str
    value: int
    max_value: int
    driver_code: DriverCode
