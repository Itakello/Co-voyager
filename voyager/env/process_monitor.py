import logging
import re
import subprocess
import threading
import time
import warnings
from typing import Callable

import psutil

import voyager.utils as U


class SubProcess:
    def __init__(
        self,
        commands: list[str],
        name: str,
        ready_match: str = r".*",
        log_path: str = "logs",
        callback_match: str = r"^(?!x)x$",  # regex that will never match
        callback: Callable = None,
        finished_callback: Callable = None,
        ready_event: threading.Event = None,
        thread: threading.Thread = None,
    ):
        self.commands = commands
        self.name = name
        self.logger = logging.getLogger(name)
        self.ready_match = ready_match
        self.logger = self._get_logger(log_path)
        self.process = None
        self.ready_event = ready_event
        self.ready_line = ""
        self.callback_match = callback_match
        self.callback = callback
        self.finished_callback = finished_callback
        self.thread = thread

    def _get_logger(self, log_path: str) -> logging.Logger:
        logger = logging.getLogger(self.name)
        start_time = time.strftime("%Y%m%d_%H%M%S")
        handler = logging.FileHandler(U.f_join(log_path, f"{start_time}.log"))
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def start(self) -> None:
        self.logger.info(f"**STARTING SUBPROCESS**\nCommands: {self.commands}")
        self.ready_event = threading.Event()
        self.ready_line = ""
        self.thread = threading.Thread(target=self._start_thread_fun)
        self.thread.start()
        self.ready_event.wait()

    def stop(self) -> None:
        self.logger.info("**STOPPING SUBPROCESS**")
        if self.process and self.process.is_running():
            self.process.terminate()
            self.process.wait()

    def _start_thread_fun(self) -> None:
        self.process = psutil.Popen(
            self.commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        print(f"Subprocess {self.name} started with PID {self.process.pid}.")
        for line in iter(self.process.stdout.readline, ""):
            self.logger.info(line.strip())
            if re.search(self.ready_match, line):
                self.ready_line = line
                self.logger.info("Subprocess is ready.")
                self.ready_event.set()
            if re.search(self.callback_match, line):
                self.callback()
        if not self.ready_event.is_set():
            self.ready_event.set()
            warnings.warn(f"Subprocess {self.name} failed to start.")
        if self.finished_callback:
            self.finished_callback()

    @property
    def is_running(self):
        if self.process is None:
            return False
        return self.process.is_running()
