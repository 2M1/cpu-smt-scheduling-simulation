from simulation.tasks import Task
from typing import Optional

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

    def pop_n_tasks(self, n: int) -> list[Task]:
        n = min(n, len(self.tasks))
        return [
            self.tasks.pop(0) for _ in range(n)
        ]

    def peek_n_tasks(self, n: int) -> list[Task]:
        n = min(n, len(self.tasks))
        return self.tasks[:n]

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

