"""Compatibility shim: moved to backend.database

This file keeps the old import path working for callers that still import
`database` from the project root. It re-exports everything from
`backend.database`.
"""

from backend.database import *  # noqa: F401,F403
