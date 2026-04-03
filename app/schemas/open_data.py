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

class SDoTEnvRow(BaseModel):
    """S-DoT 개별 센서 측정 데이터 (row 배열의 요소)"""
    
    # --- 기본 정보 ---
    MODELNAME: Optional[str] = Field(None, description="모델명")
    SERIAL: Optional[str] = Field(None, description="시리얼")
    SENSING_TIME: Optional[str] = Field(None, description="센서 시간")
    REGION: Optional[str] = Field(None, description="지역구분")
    AUTONOMOUS_DISTRICT: Optional[str] = Field(None, description="자치구역")
    ADMINISTRATIVE_DISTRICT: Optional[str] = Field(None, description="행정구역")
    
    # --- 기온 및 습도 ---
    MAX_TEMP: Optional[float] = Field(None, description="최대 기온")
    AVG_TEMP: Optional[float] = Field(None, description="평균 기온")
    MIN_TEMP: Optional[float] = Field(None, description="최소 기온")
    MAX_HUMI: Optional[float] = Field(None, description="최대 상대습도")
    AVG_HUMI: Optional[float] = Field(None, description="평균 상대습도")
    MIN_HUMI: Optional[float] = Field(None, description="최소 상대습도")
    
    # --- 바람 및 조도 ---
    MAX_WIND_SPEED: Optional[float] = Field(None, description="최대 풍속")
    AVG_WIND_SPEED: Optional[float] = Field(None, description="평균 풍속")
    MIN_WIND_SPEED: Optional[float] = Field(None, description="최소 풍속")
    MAX_WIND_DIRE: Optional[float] = Field(None, description="최대 풍향")
    AVG_WIND_DIRE: Optional[float] = Field(None, description="평균 풍향")
    MIN_WIND_DIRE: Optional[float] = Field(None, description="최소 풍향")
    MAX_INTE_ILLU: Optional[float] = Field(None, description="최대 조도")
    AVG_INTE_ILLU: Optional[float] = Field(None, description="평균 조도")
    MIN_INTE_ILLU: Optional[float] = Field(None, description="최소 조도")
    
    MAX_ULTRA_RAYS: Optional[float] = Field(None, description="최대 자외선")
    AVG_ULTRA_RAYS: Optional[float] = Field(None, description="평균 자외선")
    MIN_ULTRA_RAYS: Optional[float] = Field(None, description="최소 자외선")
    MAX_NOISE: Optional[float] = Field(None, description="최대 소음")
    AVG_NOISE: Optional[float] = Field(None, description="평균 소음")
    MIN_NOISE: Optional[float] = Field(None, description="최소 소음")
    MAX_VIBR_X: Optional[float] = Field(None, description="최대 진동(x)")
    AVG_VIBR_X: Optional[float] = Field(None, description="평균 진동(x)")
    MIN_VIBR_X: Optional[float] = Field(None, description="최소 진동(x)")
    MAX_VIBR_Y: Optional[float] = Field(None, description="최대 진동(y)")
    AVG_VIBR_Y: Optional[float] = Field(None, description="평균 진동(y)")
    MIN_VIBR_Y: Optional[float] = Field(None, description="최소 진동(y)")
    MAX_VIBR_Z: Optional[float] = Field(None, description="최대 진동(z)")
    AVG_VIBR_Z: Optional[float] = Field(None, description="평균 진동(z)")
    MIN_VIBR_Z: Optional[float] = Field(None, description="최소 진동(z)")
    
    # --- 체감/흑구온도 ---
    MAX_EFFE_TEMP: Optional[float] = Field(None, description="최대 흑구온도")
    AVG_EFFE_TEMP: Optional[float] = Field(None, description="평균 흑구온도")
    MIN_EFFE_TEMP: Optional[float] = Field(None, description="최소 흑구온도")
    
    # --- 화학물질 및 대기질 ---
    MAX_NO2: Optional[float] = Field(None, description="최대 이산화질소")
    AVG_NO2: Optional[float] = Field(None, description="평균 이산화질소")
    MIN_NO2: Optional[float] = Field(None, description="최소 이산화질소")
    MAX_CO: Optional[float] = Field(None, description="최대 일산화탄소")
    AVG_CO: Optional[float] = Field(None, description="평균 일산화탄소")
    MIN_CO: Optional[float] = Field(None, description="최소 일산화탄소")
    MAX_SO2: Optional[float] = Field(None, description="최대 이산화황")
    AVG_SO2: Optional[float] = Field(None, description="평균 이산화황")
    MIN_SO2: Optional[float] = Field(None, description="최소 이산화황")
    MAX_NH3: Optional[float] = Field(None, description="최대 암모니아")
    AVG_NH3: Optional[float] = Field(None, description="평균 암모니아")
    MIN_NH3: Optional[float] = Field(None, description="최소 암모니아")
    MAX_H2S: Optional[float] = Field(None, description="최대 황화수소")
    AVG_H2S: Optional[float] = Field(None, description="평균 황화수소")
    MIN_H2S: Optional[float] = Field(None, description="최소 황화수소")
    MAX_O3: Optional[float] = Field(None, description="최대 오존")
    AVG_O3: Optional[float] = Field(None, description="평균 오존")
    MIN_O3: Optional[float] = Field(None, description="최소 오존")
    
    DATE: Optional[str] = Field(None, description="데이터수집시간")
    DATA_NO: Optional[str] = Field(None, description="데이터구분번호")

    @model_validator(mode='before')
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, str) and val.strip() == "":
                    data[key] = None
        return data
    
class sDoTEnvResponse(OpenDataItem):
    """스마트서울 도시데이터 센서(S-DoT) 환경정보 (실시간) 구조체"""
    row: List[SDoTEnvRow] = Field(..., description="센서 데이터 리스트")

class CulturalEventRow(BaseModel):
    """서울시 문화행사 정보 (row 배열의 요소)"""
    
    CODENAME: Optional[str] = Field(None, description="분류")
    GUNAME: Optional[str] = Field(None, description="자치구")
    TITLE: Optional[str] = Field(None, description="공연/행사명")
    DATE: Optional[str] = Field(None, description="날짜")
    PLACE: Optional[str] = Field(None, description="장소")
    ORG_NAME: Optional[str] = Field(None, description="기관명")
    USE_TRGT: Optional[str] = Field(None, description="이용대상")
    USE_FEE: Optional[str] = Field(None, description="이용요금")
    INQUIRY: Optional[str] = Field(None, description="문의")
    PLAYER: Optional[str] = Field(None, description="출연자정보")
    PROGRAM: Optional[str] = Field(None, description="프로그램소개")
    ETC_DESC: Optional[str] = Field(None, description="기타내용")
    ORG_LINK: Optional[str] = Field(None, description="홈페이지 주소")
    MAIN_IMG: Optional[str] = Field(None, description="대표이미지")
    RGSTDATE: Optional[str] = Field(None, description="신청일")
    TICKET: Optional[str] = Field(None, description="시민/기관")
    STRTDATE: Optional[str] = Field(None, description="시작일")
    END_DATE: Optional[str] = Field(None, description="종료일")
    THEMECODE: Optional[str] = Field(None, description="테마분류")
    
    LOT: Optional[float] = Field(None, description="경도(Y좌표)")
    LAT: Optional[float] = Field(None, description="위도(X좌표)")
    
    IS_FREE: Optional[str] = Field(None, description="유무료")
    HMPG_ADDR: Optional[str] = Field(None, description="문화포털상세URL")
    PRO_TIME: Optional[str] = Field(None, description="행사시간")

    @model_validator(mode='before')
    @classmethod
    def empty_str_to_none(cls, data: Any) -> Any:
        """빈 문자열을 None으로 치환하여 float 파싱 에러(LAT, LOT) 방지"""
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, str) and val.strip() == "":
                    data[key] = None
        return data

class CulturalEventResponse(OpenDataItem):
    row: List[CulturalEventRow] = Field(default_factory=list, description="문화행사 데이터 리스트")