from datetime import datetime
from typing import List
from fastapi.encoders import jsonable_encoder
from app.core.configs import get_logger, get_environment
from app.core.exceptions import NotFoundError

_logger = get_logger(__name__)
_env = get_environment()


class ManagementAPI: