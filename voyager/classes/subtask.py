from dataclasses import dataclass


@dataclass
class SubTask:
    content: str
    tool: str = "None"
    materials: str = "None"
