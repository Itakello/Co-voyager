from dataclasses import dataclass, field

from voyager.classes import Material, Status


@dataclass
class SubTask:

    action: str
    item: str
    quantity: int
    content: str = ""
    content_doing: str = ""
    tools: list[str] = field(default_factory=list)
    materials: list[Material] = field(default_factory=list)
    status: Status = Status.BLOCKED

    def __init__(
        self,
        action: str,
        item: str,
        quantity: int,
        tools: str = "None",
        materials: str = "None",
    ) -> None:
        assert action in [
            "craft",
            "gather",
            "kill",
            "shoot",
            "smelt",
            "build",
        ], "Invalid action."
        self.action = action
        self.item = self._turn_singular(item)
        self.quantity = quantity
        self.tools = [] if tools == "None" else tools.split(", ")
        self.materials = [] if materials == "None" else self._parse_materials(materials)

    def generate_content(self) -> None:
        self.content = f"{self.action.capitalize()} {self.quantity} {self.item}"
        if self.item in ["crafting table", "furnace"]:
            if self.action not in ["craft", "build"]:
                raise ValueError(f"Invalid action {self.action} for item {self.item}.")
            if self.item == "crafting table":
                self.content += " and place it on the ground 1 block left the chest."
            else:
                self.content += " and place it on the ground 1 block right the chest."

        elif self.action in ["gather", "craft", "smelt"]:
            self.content += " and place it/them in the chest."
        elif self.action == "kill":
            self.content += " using killMob (already present)."
        if self.tools != []:
            if self.tools[0] not in ["crafting table", "furnace"]:
                tools = " and the ".join(self.tools)
                self.content += f" Then place the {tools} back in the chest."

        self.content_doing = f"{self.action}ing {self.quantity} {self.item}"

    def __str__(self) -> str:
        return f"{self.content} ({self.status.value})"

    def _parse_materials(self, materials_str: str) -> list[Material]:
        splitted_materials = materials_str.split(", ")
        materials = []
        for material in splitted_materials:
            material = material.split(" ")
            quantity = int(material[0])
            name = " ".join(material[1:]).strip()
            name = self._turn_singular(name)
            materials.append(Material(name=name, quantity=quantity))
        return materials

    def _turn_singular(self, word: str) -> str:
        if word.endswith("s"):
            return word[:-1]
        return word

    def update_statuses_to_ready(self, inventory: dict) -> None:
        if self.status != Status.BLOCKED:
            return
        required_tools = all(tool in inventory for tool in self.tools)
        required_materials = all(
            material.name in inventory for material in self.materials
        )
        if required_tools and required_materials:
            self.status = Status.READY
