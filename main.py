from dataclasses import  dataclass, field
from enum import auto, Enum
from typing import Optional, Annotated, Callable, Any
from pprint import pprint

from simulation.tasks import Task, TaskCategory, InstructionType

import matplotlib.colors
import matplotlib.pyplot as plt
from matplotlib import  colormaps


QUNATUM_NUM_CYCLES = 0 # TODO
SMT_MAX = 4


N_THREADS = 5

class RunQueue:
    tasks: list[Task]
    _iter_indices: dict[int, int]
    _prev_index: int

    def __init__(self, tasks: Optional[list[Task]] = None):
        self.tasks = tasks or []
        self.reset_indices()

    def add_task(self, task: Task):
        self.tasks.append(task)

    def add_tasks(self, tasks: list[Task]):
        self.tasks.extend(tasks)

    def peek_four(self) -> list[Task]:
        return self.tasks[:4]

    def pop_four(self) -> list[Task]:
        return [
            self.tasks.pop(0) for _ in range(4)
        ]

    def peek_two(self) -> list[Task]:
        return self.tasks[:2]

    def pop_two(self) -> list[Task]:
        return [
            self.tasks.pop(0) for _ in range(2)
        ]

    def peek_task(self) -> list[Task]:
        return [self.tasks[0]]

    def pop_task(self) -> list[Task]:
        return [self.tasks.pop(0)]

    def is_empty(self) -> bool:
        return len(self.tasks) == 0

    def reset_indices(self):
        self._iter_indices = {
            1: 0,
            2: 0,
            4: 0,
        }
        self._prev_index = 0

    def _peek_prev_with_size(self, size: int) -> Optional[Task]:
        if self._iter_indices[size] == len(self.tasks):
            return None

        while self.tasks[len(self.tasks) - 1 - self._iter_indices[size]].category.value.slots_filled != size:
            self._iter_indices[size] += 1

            if self._iter_indices[size] == len(self.tasks):
                return None

        self._iter_indices[size] += 1
        return self.tasks[len(self.tasks) - 1 - self._iter_indices[size]]

    def peek_prev(self) -> Optional[Task]:
        if self._prev_index == len(self.tasks):
            return None

        last = self.tasks[len(self.tasks) -1 - self._prev_index]
        self._prev_index += 1
        return last

    def peek_prev_single_width(self) -> Optional[Task]:
       return self._peek_prev_with_size(1)

    def peek_prev_double_width(self) -> Optional[Task]:
       return self._peek_prev_with_size(2)

    def peek_prev_four_width(self) -> Optional[Task]:
       return self._peek_prev_with_size(4)

    def __len__(self):
        return len(self.tasks)


def pop_run_instructions_from_task(task: Task, quantumSMT: int) -> None:
    task.remaining_instructions.pop(0)


def run_simulation_to_exhaustion(
    tasks: list[tuple[TimeQuantum, Task]],
    scheduling_algorithm: Callable[[RunQueue], list[Task]],

) -> dict[TimeQuantum, list[Task]]:

    run_queue = RunQueue(list(map(lambda t: t[1], filter(lambda t: t[0] == 0, tasks)))) # initialise with tasks arriving at start
    run_order = {}

    quantum = 0
    while not run_queue.is_empty():
        scheduled_tasks = scheduling_algorithm(run_queue)
        quantum_smt = len(scheduled_tasks)
        assert quantum_smt in (1, 2, 4)

        run_order[quantum] = scheduled_tasks

        quantum += 1
        new_tasks = filter(lambda t: t[0] == quantum, tasks)
        for _, task in new_tasks:
            run_queue.add_task(task)

        for task in scheduled_tasks:
            pop_run_instructions_from_task(task, quantum_smt)
            task.run_at.append(quantum)
            if task.remaining_instructions:
                run_queue.add_task(task)

    return run_order


def round_robin_smt4(run_queue: RunQueue) -> list[Task]:
    if len(run_queue) < 4:
        if len(run_queue) < 2:
            return run_queue.pop_task()
        return run_queue.pop_two()
    return run_queue.pop_four()


def slot_fill_shed(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    if len(run_queue) < 2:
        return run_queue.pop_task()

    run_queue.reset_indices()
    top = run_queue.pop_task()[0]
    remaining = SMT_MAX - top.category.value.slots_filled
    print(f"Top task {top.id} width {top.category.value.slots_filled} means {remaining} slots remaining")
    if remaining <= 1:
        return [top] # no more room
    elif remaining == 2:
        # must select a single thread with size two
        last = run_queue.peek_task()[0]
        index = len(run_queue.tasks) - 2
        while last.category.value.slots_filled != 2:
            if index < 0:
                # only tasks with slot-width 1 remaining, pick the most current one
                return [top, run_queue.pop_task()[0]]
            last = run_queue.tasks[index]
            index -= 1

        run_queue.tasks.remove(last)
        return [top, last]
    else: # remaining = 3: Select 3 threads with width 1 or one with 1 and fill remainder
        selected = []
        while len(selected) < 3:

            last = run_queue.peek_prev_single_width()
            if last is None:
                break

            selected.append(last)

        if len(selected) < 3:
            # search for a task with width two to fill the slot:
            if len(selected) == 2:
                # fill with any remaining:
                while last := run_queue.peek_prev():
                    if last is None:
                        break

                    if last not in selected:
                        selected.append(last)
                        break

                if len(selected) == 2:
                    # only three tasks remaining, can only run two at a time.
                    # remove last added task since we cannot run 3
                    selected.pop()

        print(list(map(lambda t: t.id, selected)), top.id)
        for task in selected:
            run_queue.tasks.remove(task)

        selected.insert(0, top)
        return selected


def even_slot_scheduling(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()
    if len(run_queue) == 1:
        return run_queue.pop_task()




def plot_schedule_processor_view(timeline: dict[TimeQuantum, list[Task]], algorithm: str = "Round Robin"):
    # we are passing all tasks multiple times. But since this is not a performant application this is not important.
    fig, ax = plt.subplots()

    current_time = 0
    appearances = set()
    height = 2.0

    for time, tasks  in timeline.items():

        n_smt = len(tasks)
        delta_y = height / n_smt
        for i, task in enumerate(tasks):
            fill = ax.fill_between(
                [current_time, current_time + 1],
                [(i+1) * delta_y,  (i+1)*delta_y],
                i*delta_y,
                facecolor=task.colour,
            )
            if task.id not in appearances:
                fill.set_label(f"Task {task.id}")
                appearances.add(task.id)

        current_time += 1
    ax.set_ylim(0, height*2)
    ax.set_xlim(0, current_time+1)
    ax.set_xlabel('Time-quantum')
    ax.xaxis.set_ticks(range(current_time+1))
    ax.set_yticks([height/8 * i for i in range(1, 9, 2)])
    ax.set_yticklabels(['HW Thread 1', 'HW Thread 2', 'HW Thread 3', 'HW Thread 4'])
    ax.legend(loc="upper left")
    ax.grid(True)
    ax.set_title(f'Thread Scheduling Timeline ({algorithm})')
    plt.show()


def calculate_statistics(timeline: dict[TimeQuantum, list[Task]]) -> dict[str, Any]:
    return {}


if __name__ == '__main__':
    res = run_simulation_to_exhaustion([
        (0, Task(0, TaskCategory.MEM,
                 [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM] * 2)),
        (0, Task(1, TaskCategory.MEM,
                 [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM] * 2)),
        (0, Task(2, TaskCategory.MEM,
                 [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
        (0, Task(3, TaskCategory.MEM,
                 [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
        (0, Task(4, TaskCategory.MEM, [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
        # (0, Task("orange", TaskCategory.MEM, [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    ],
        slot_fill_shed)

    plot_schedule_processor_view(res, "Slot Fill Scheduling")

