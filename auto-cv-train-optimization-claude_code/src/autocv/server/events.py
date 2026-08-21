"""駕駛艙 WebSocket 事件資料結構。"""

from __future__ import annotations

from dataclasses import dataclass, field

KINDS = ("stage", "log", "metric", "await_confirm", "result", "done")


@dataclass
class Event:
    kind: str
    stage: str = ""
    payload: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"kind": self.kind, "stage": self.stage, "payload": self.payload}
