import os
from dataclasses import  dataclass, field
from enum import auto, Enum

from simulation.display import get_task_color

N_THREADS = int(os.getenv("N_THREADS", 8))

type TimeQuantum = int

@dataclass
class TaskCategoryCharacteristics:
    speedup: float = 1.0
    slots_filled: int = 1

class InstructionType(Enum):
    ALU = auto()
    MEM = auto()
    IO = auto()
    FP = auto()


class TaskCategory(Enum):
    ALU = TaskCategoryCharacteristics(1.0, 2)
    MEM = TaskCategoryCharacteristics(1.0)
    IO = TaskCategoryCharacteristics(1.0)
    FP = TaskCategoryCharacteristics(1.0, 2)


@dataclass
class Task:
    id: int
    category: TaskCategory
    remaining_instructions: list[InstructionType]
    colour: str = ""
    run_at: list[TimeQuantum] = field(default_factory=list)

    def __post_init__(self):
        self.colour = get_task_color(self.id, N_THREADS)
        print(
            f"Task {self.id} has colour {self.colour}"
        )

