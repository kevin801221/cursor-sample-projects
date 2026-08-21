"""背景 thread 跑 pipeline，發事件到 queue，train/optimize 前 GO-gate 阻塞。"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Optional

from autocv.server.events import Event

GATED = {"train", "optimize"}


@dataclass
class Stage:
    name: str
    run: Callable[[Callable[[Event], None]], None]
    estimate: Optional[Callable[[], float]] = None
    detail: str = ""


@dataclass
class PipelineRunner:
    stages: list[Stage]
    events: "queue.Queue[Event]" = field(default_factory=queue.Queue)
    status: str = "idle"
    _gate: threading.Event = field(default_factory=threading.Event)
    _thread: Optional[threading.Thread] = None

    def _emit(self, ev: Event) -> None:
        self.events.put(ev)

    def confirm(self) -> None:
        self._gate.set()

    def start(self) -> None:
        if self.status == "running":
            raise RuntimeError("已有 pipeline 在跑")
        self.status = "running"
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self) -> None:
        try:
            for st in self.stages:
                self._emit(Event("stage", st.name, {"status": "running"}))
                if st.name in GATED:
                    est = st.estimate() if st.estimate else 0.0
                    self._gate.clear()
                    self._emit(
                        Event(
                            "await_confirm",
                            st.name,
                            {"estimate_min": est, "detail": st.detail},
                        )
                    )
                    self._gate.wait()
                st.run(self._emit)
                self._emit(Event("stage", st.name, {"status": "done"}))
            self.status = "done"
            self._emit(Event("done", "", {"ok": True}))
        except Exception as exc:  # noqa: BLE001
            self.status = "error"
            self._emit(Event("done", "", {"ok": False, "error": str(exc)}))
