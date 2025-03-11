import matplotlib.pyplot as plt
from matplotlib import colormaps
from . import TimeQuantum
from simulation.tasks import Task


def plot_schedule_processor_view(timeline: dict[TimeQuantum, list[Task]], algorithm: str = "Round Robin"):
    # we are passing all tasks multiple times. But since this is not a performant application this is not important.
    fig, ax = plt.subplots()

    current_time = 0
    appearances = set()
    height = 2.0

    for time, tasks in timeline.items():

        n_smt = len(tasks)
        # new_tasks = []
        # for task in tasks:
        #     new_tasks.extend([task] * task.category.value.slots_filled)
        # tasks = new_tasks
        delta_y = height / n_smt
        for i, task in enumerate(tasks):
            fill = ax.fill_between(
                [current_time, current_time + 1],
                [(i + 1) * delta_y, (i + 1) * delta_y],
                i * delta_y,
                facecolor=task.colour,
            )
            if task.id not in appearances:
                fill.set_label(f"Task {task.id}")
                appearances.add(task.id)

        current_time += 1
    ax.set_ylim(0, height * 2)
    ax.set_xlim(0, current_time + 1)
    ax.set_xlabel('Time-quantum')
    ax.xaxis.set_ticks(range(current_time + 1))
    ax.set_yticks([height / 8 * i for i in range(1, 9, 2)])
    ax.set_yticklabels(['HW Thread 1', 'HW Thread 2', 'HW Thread 3', 'HW Thread 4'])
    ax.legend(loc="upper left")
    ax.grid(True)
    ax.set_title(f'Thread Scheduling Timeline ({algorithm})')
    plt.show()
