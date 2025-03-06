from matplotlib import colormaps


colors = colormaps['tab20c']


def get_task_color(task_id: int, total_tasks: int) -> str:
    return colors(float(task_id) / total_tasks)
