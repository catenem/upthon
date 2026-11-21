"""Versão de terminal do Upthon (sem front).   python upthon.py [--root PASTA]"""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

from app.cli.app import CliApp
from app.cli.console import Console
from app.cli.settings_store import CliConfig
from app.container import Container
from app.core.config import get_settings
from app.core.logging import setup_logging


async def main(root: Path | None) -> None:
    settings = get_settings()
    setup_logging(logging.INFO)
    container = Container(settings)
    await container.startup()
    try:
        config = CliConfig(settings.base_dir / "cli_config.json")
        if root:
            config.save_root(root)
        await CliApp(container, Console(), config).run()
    finally:
        await container.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upthon (terminal)")
    parser.add_argument("--root", type=Path, help="pasta raiz com os cursos (fica salva)")
    args = parser.parse_args()
    try:
        asyncio.run(main(args.root.resolve() if args.root else None))
    except KeyboardInterrupt:
        print("\nInterrompido. Se havia upload em andamento, retome em 'p' (pendentes).")
