import os
import sys
# 현재 스크립트의 상위 경로를 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pydantic import BaseModel, Field
import re

from app.formatter.code_formatter import parse_augmented_chunk

# 테스트 데이터
response_text = """
Here is the augmented code chunk with added contextual information:

<augmented_chunk>
<metadata>
<function_name>detachSensorFromOtherPartitions</function_name>
<summary>Detaches a given sensor from all cage partitions it is associated with.</summary>
<features>
- Retrieves a list of cage partitions associated with the sensor
- Iterates through the list of partitions
- Detaches the sensor from each partition
- Uses the Optional class to handle null values
</features>
</metadata>
<code>
private void detachSensorFromOtherPartitions(MoSensor moSensor) {

Optional<List<MoCagePartition>> optionalPartitions = moCagePartitionRepository.findBySensor(moSensor);

if (optionalPartitions.isPresent()) {
List<MoCagePartition> partitions = optionalPartitions.get();
for (MoCagePartition partition : partitions) {

detachSensorFromPartition(partition);
}
}
}
</code>
</augmented_chunk>
"""

# 파싱 실행
parsed_chunk = parse_augmented_chunk(response_text)

# JSON 형식으로 출력
# print(parsed_chunk.json(indent=4))

import json

# 기존 Pydantic 모델의 JSON 출력을 기본 방식으로 출력한 후, json.loads와 dumps를 사용하여 들여쓰기 적용
parsed_json = json.loads(parsed_chunk.json())  # Pydantic v2의 기본 json 메서드를 사용해 JSON으로 변환
formatted_json = json.dumps(parsed_json, indent=4)  # 원하는 들여쓰기 적용
print(formatted_json)
print("--------------------------------")
print(parsed_json.get("summary"))