# tests/tasks/collectors/test_open_data.py

import pytest
from app.tasks.collectors.open_data import collect_cultural_event_info, collect_sDoTEnv
from app.schemas.open_data import CulturalEventRow, SDoTEnvRow

@pytest.mark.asyncio
async def test_collect_sDoTEnv_integration():
    start_idx = 1
    end_idx = 5
    
    result_data = await collect_sDoTEnv(start_idx, end_idx)
    
    assert result_data is not None
    assert isinstance(result_data, list)
    assert len(result_data) <= 5 
    
    if len(result_data) > 0:
        first_item = result_data[0]
        
        print(f"\n========== [S-DoT 데이터 ({len(result_data)}건 수집됨)] ==========")
        print(first_item.model_dump_json(indent=2))
        print("==================================================\n")
        
        assert isinstance(first_item, SDoTEnvRow)
        
        if first_item.MAX_TEMP is not None:
            assert isinstance(first_item.MAX_TEMP, float)

@pytest.mark.asyncio
async def test_collect_cultural_events_integration():
    """
    서울시 문화행사 정보 API가 정상적으로 호출되고, 
    CulturalEventRow Pydantic 구조체로 완벽하게 파싱되는지 검증
    """
    start_idx = 1
    end_idx = 5
    
    result_data = await collect_cultural_event_info(start_idx, end_idx)

    assert result_data is not None
    assert isinstance(result_data, list)
    assert len(result_data) <= 5 
    
    if len(result_data) > 0:
        first_item = result_data[0]

        print(f"\n========== [문화행사 데이터 ({len(result_data)}건 수집됨)] ==========")
        print(first_item.model_dump_json(indent=2))
        print("====================================================\n")
        
        assert isinstance(first_item, CulturalEventRow)
        
        if first_item.LAT is not None:
            assert isinstance(first_item.LAT, float)
        if first_item.LOT is not None:
            assert isinstance(first_item.LOT, float)