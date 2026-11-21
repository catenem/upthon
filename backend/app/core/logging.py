from __future__ import annotations

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("telethon").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # a URL do httpx contém o token do bot
