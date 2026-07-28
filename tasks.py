"""Compatibility shim: moved to backend.tasks

Re-exports task settings and functions from backend.tasks to keep
`arq tasks.WorkerSettings` working with the old import path.
"""

from backend.tasks import *  # noqa: F401,F403
