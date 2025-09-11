"""Celery utilities for task management without direct imports."""

from celery import current_app


def get_task(task_name: str):
    """Get a Celery task by name without importing it."""
    return current_app.tasks.get(task_name)
