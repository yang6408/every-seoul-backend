from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

class SeoulApiResultCode(str, Enum):
    SUCCESS = "INFO-000"
    MISSING_PARAM = "ERROR-300"
    AUTH_ERROR = "INFO-100"
    INVALID_TYPE = "ERROR-301"
    NOT_FOUND_SERVICE = "ERROR-310"
    INVALID_START = "ERROR-331"
    INVALID_END = "ERROR-332"
    INVALID_RANGE_TYPE = "ERROR-333"
    INVALID_RANGE = "ERROR-334"
    LIMIT_EXCEEDED_SAMPLE = "ERROR-335"
    LIMIT_EXCEEDED = "ERROR-336"
    SERVER_ERROR = "ERROR-500"
    DB_ERROR = "ERROR-600"
    SQL_ERROR = "ERROR-601"
    NO_DATA = "INFO-200"

class OpenDataItem(BaseModel):
    """서울시 공공데이터 구조체"""
    list_total_count: int
    RESULT_CODE: SeoulApiResultCode = Field(..., description="요청결과 코드")
    RESULT_MESSAGE: str = Field(..., description="요청결과 메시지")
