from simulation.tasks import Task, TaskCategory
from simulation.runqueue import RunQueue
from simulation import N_THREADS as SMT_MAX


def round_robin_smt4(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    return run_queue.pop_n_tasks(SMT_MAX)


def slot_fill_shed(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    if len(run_queue) < 2:
        return run_queue.pop_task()

    run_queue.reset_indices()
    top = run_queue.pop_task()[0]
    remaining = SMT_MAX - top.category.value.slots_filled
    selected = [top]
    if remaining <= 1:
        return [top]  # no more room

    while remaining > 1:
        next = run_queue.peek_next()
        if next is None:
            break
        if next.category.value.slots_filled > remaining:
            continue

        selected.append(run_queue.pop_task()[0])
        remaining -= next.category.value.slots_filled

    return selected

    # must select a single thread with size two
    #     last = run_queue.peek_task()[0]
    #     index = len(run_queue.tasks) - 2
    #     while last.category.value.slots_filled != 2:
    #         if index < 0:
    #             # only tasks with slot-width 1 remaining, pick the most current one
    #             return [top, run_queue.pop_task()[0]]
    #         last = run_queue.tasks[index]
    #         index -= 1
    #
    #     run_queue.tasks.remove(last)
    #     return [top, last]
    # else:  # remaining = 3: Select 3 threads with width 1 or one with 1 and fill remainder
    #     selected = []
    #     while len(selected) < 3:
    #
    #         last = run_queue.peek_prev_single_width()
    #         if last is None:
    #             break
    #
    #         selected.append(last)
    #
    #     if len(selected) < 3:
    #         # search for a task with width two to fill the slot:
    #         if len(selected) == 2:
    #             # fill with any remaining:
    #             while last := run_queue.peek_prev():
    #                 if last is None:
    #                     break
    #
    #                 if last not in selected:
    #                     selected.append(last)
    #                     break
    #
    #             if len(selected) == 2:
    #                 # only three tasks remaining, can only run two at a time.
    #                 # remove last added task since we cannot run 3
    #                 selected.pop()
    #
    #     for task in selected:
    #         run_queue.tasks.remove(task)
    #
    #     selected.insert(0, top)
    #     return selected
    #


def score_scheduling(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    if len(run_queue) <= SMT_MAX:
        return run_queue.pop_n_tasks(SMT_MAX)

    selected = run_queue.pop_task()
    duplicate_penalty = 2.0
    # from the next four, select the one with the least duplicate
    # score:
    type_counts = {selected[0].category: 1}
    while len(selected) < 4:
        next_tasks = run_queue.peek_n_tasks(4)
        if not next_tasks:
            # no more tasks
            break
        if len(next_tasks) <= SMT_MAX - len(selected):
            selected.extend(run_queue.pop_n_tasks(len(next_tasks)))
            break
        print(len(next_tasks))
        scores = [1] * len(next_tasks)
        for i, task in enumerate(next_tasks):
            scores[i] = (type_counts.get(task.category, 1) - 1) * duplicate_penalty

        print(scores)
        lowest_score_task = next_tasks[scores.index(min(scores))]
        selected.append(lowest_score_task)
        type_counts[lowest_score_task.category] = type_counts.get(lowest_score_task.category, 0) + 1
        run_queue.pop_specific_task(lowest_score_task)

    return selected
