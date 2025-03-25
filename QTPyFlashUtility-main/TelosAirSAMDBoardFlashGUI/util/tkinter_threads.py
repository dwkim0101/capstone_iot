from threading import Event, Thread
from TelosAirSAMDBoardFlashGUI.context import CONTEXT
from typing import Callable

class JobThread(Thread):
    def __init__(self, done_event_signals: 'list[str]', task_func: Callable):
        super().__init__(daemon=True)
        self.signal_done = lambda: [CONTEXT.root.event_generate(s) for s in done_event_signals]
        self.task_func = task_func

    def run(self):
        try:
            self.task_func()
        except Exception:
            pass

        self.signal_done()