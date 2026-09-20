"""ASGI entry point for Uvicorn."""

from ops_pilot.application import create_app

app = create_app()
