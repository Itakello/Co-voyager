from dataclasses import dataclass

import voyager.utils as U
from voyager.classes.subtask import SubTask


@dataclass
class Task:

    name: str
    content: str
    sub_tasks: list[SubTask]

    def __post_init__(self):
        self.path = f"tasks/{self.name}"
        if not U.file_utils.f_exists(self.path):
            U.file_utils.f_mkdir(self.path)
        self.skills_folder = f"{self.path}/skills"
        if not U.file_utils.f_exists(self.skills_folder):
            U.file_utils.f_mkdir(self.skills_folder)
