from __future__ import annotations

from typing import Union

from fastapi import Header

from app.core.configs import get_logger


_logger = get_logger(__name__)


async def check_current_organization(
    x_organization: Union[str, None] = Header(
        default=None
    ),
) -> str:
    if x_organization:
        _logger.info(f"Using organization {x_organization}")

    else:
        _logger.info(f"User not using any organization")

    return x_organization
