from dataclasses import dataclass, field
from enum import auto, Enum
from pathlib import Path
from typing import Optional, Annotated, Callable, Any
from pprint import pprint

from simulation.load_exec import load_exec_dump
from simulation.pipeline import PipelineStart, Pipeline
from simulation.tasks import Task, TaskCategory, InstructionType, BranchInstruction
from simulation.display import plot_schedule_processor_view
from simulation.tasks import TimeQuantum

import matplotlib.colors
import matplotlib.pyplot as plt
from matplotlib import colormaps

QUNATUM_NUM_CYCLES = 0  # TODO
SMT_MAX = 4

N_THREADS = 5


def calculate_statistics(timeline: dict[TimeQuantum, list[Task]]) -> dict[str, Any]:
    return {}


if __name__ == '__main__':
    # res = run_simulation_to_exhaustion([
    #     (0, Task(0, TaskCategory.MEM,
    #              [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM] * 2)),
    #     (0, Task(1, TaskCategory.MEM,
    #              [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM] * 2)),
    #     (0, Task(2, TaskCategory.MEM,
    #              [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    #     (0, Task(3, TaskCategory.MEM,
    #              [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    #     (0, Task(4, TaskCategory.MEM, [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    #     # (0, Task("orange", TaskCategory.MEM, [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    # ],
    #     slot_fill_shed)
    #
    # plot_schedule_processor_view(res, "Slot Fill Scheduling")
    #
    tasks = load_exec_dump(Path("workload/matrix.dump"), {"mul_row_thread": 4})
    insts = tasks[0].instructions
    print(list(
        filter(lambda i: (i.type == InstructionType.BRANCH and i.branch_mode == BranchInstruction.BranchMode.UNTIL),
               insts)
    ))
    pipeline = Pipeline(tasks)
    while not (res := pipeline.tick()):
        pass
    pprint(res)
    # print(pipeline.forward())
