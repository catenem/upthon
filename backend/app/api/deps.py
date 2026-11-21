from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.container import Container
from app.core.errors import ServiceUnavailable


def get_container(request: Request) -> Container:
    container = getattr(request.app.state, "container", None)
    if container is None:
        raise ServiceUnavailable("Controller não inicializado")
    return container


ContainerDep = Annotated[Container, Depends(get_container)]
