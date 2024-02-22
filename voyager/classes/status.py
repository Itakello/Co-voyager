from enum import Enum


class Status(Enum):
    BLOCKED = "blocked"
    READY = "ready"
    IN_PROGRESS = "in progress"
    DONE = "done"
