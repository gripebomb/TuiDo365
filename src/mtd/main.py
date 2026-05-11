"""Entrypoint for the ``mtd`` console script."""

from __future__ import annotations

from mtd.cli.app import app


def main() -> None:
    app()
