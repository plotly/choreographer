from __future__ import annotations

import queue
import threading
from concurrent.futures import Executor, Future
from typing import TYPE_CHECKING

import logistro

if TYPE_CHECKING:
    from typing import Any, Callable, TypeVar

    try:
        from typing import ParamSpec
    except ImportError:
        from typing_extensions import ParamSpec

    _P = ParamSpec("_P")  # Runtime special generic that gives you access to fn sig
    _T = TypeVar("_T")


_logger = logistro.getLogger(__name__)


class ExecutorClosedError(RuntimeError):
    """Raise if submitting when executor is closed."""


class ManualThreadExecutor(Executor):
    def __init__(
        self,
        *,
        max_workers: int = 2,
        daemon: bool = True,
        name: str = "manual-exec",
    ) -> None:
        self._q: queue.Queue[
            tuple[  # could be typed more specifically if singleton @ submit()
                Callable[..., Any],
                Any,
                Any,
                Future[Any],
            ]
            | None
        ] = queue.Queue()
        self._stop = False
        self._threads = []
        self.name = name
        for i in range(max_workers):
            t = threading.Thread(
                target=self._worker,
                name=f"{name}-{i}",
                daemon=daemon,
            )
            t.start()
            self._threads.append(t)

    def _worker(self) -> None:
        while True:
            item = self._q.get()
            if item is None:  # sentinel
                return
            fn, args, kwargs, fut = item
            if fut.set_running_or_notify_cancel():
                try:
                    res = fn(*args, **kwargs)
                except BaseException as e:  # noqa: BLE001 yes we catch and set
                    fut.set_exception(e)
                else:
                    fut.set_result(res)
            self._q.task_done()

    # _T is generic so we can mar
    def submit(
        self,
        fn: Callable[_P, _T],
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> Future[_T]:
        fut: Future[_T] = Future()
        if self._stop:
            fut.set_exception(ExecutorClosedError("Cannot submit tasks."))
            return fut
        self._q.put((fn, args, kwargs, fut))
        return fut

    def shutdown(
        self,
        wait: bool = True,  # noqa: FBT001, FBT002 overriding, can't change args
        *,
        cancel_futures: bool = False,
    ) -> None:
        self._stop = True
        if cancel_futures:
            # Drain queue and cancel pending
            try:
                while True:
                    full = self._q.get_nowait()
                    if full is not None:
                        _, _, _, fut = full
                        fut.cancel()
                    self._q.task_done()
            except queue.Empty:
                pass
        for _ in self._threads:
            self._q.put(None)
        if wait:
            for t in self._threads:
                t.join(timeout=2.0)
