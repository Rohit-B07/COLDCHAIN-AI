"""Backend startup entrypoint.

Runs the FastAPI application under uvicorn. On Windows, the default
``ProactorEventLoop`` is incompatible with psycopg async mode, so the selector
event-loop policy is installed here - before uvicorn creates any event loop -
rather than inside an imported application module.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn  # noqa: E402  (imported after the policy is set)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)
