

### 명령어 모음

#### 1. 클러스터 상태 확인

curl -X GET "http://localhost:9200/_cluster/health?pretty"


⸻

#### 2. 전체 인덱스 목록 확인

curl -X GET "http://localhost:9200/_cat/indices?v"


⸻

#### 3. 특정 인덱스의 매핑 정보 확인

curl -X GET "http://localhost:9200/{index_name}/_mapping?pretty"

예:

curl -X GET "http://localhost:9200/manual_document/_mapping?pretty"


⸻

#### 4. 특정 인덱스의 데이터 조회 (기본 10건)

curl -X GET "http://localhost:9200/{index_name}/_search?pretty"

예:

curl -X GET "http://localhost:9200/manual_document/_search?pretty"


⸻

#### 5. match_all 쿼리로 전체 조회

curl -X GET "http://localhost:9200/{index_name}/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  }
}'


⸻

#### 6. 특정 필드로 match 검색

curl -X GET "http://localhost:9200/{index_name}/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "필드명": "검색어"
    }
  }
}'

예:

curl -X GET "http://localhost:9200/manual_document/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "title": "매뉴얼"
    }
  }
}'


⸻

#### 7. 문서 ID로 조회

curl -X GET "http://localhost:9200/{index_name}/_doc/{document_id}?pretty"


⸻

#### 8. 쿼리 결과 개수 제한 (size)

curl -X GET "http://localhost:9200/{index_name}/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "size": 5,
  "query": {
    "match_all": {}
  }
}'


⸻

#### 9. 쿼리 결과에서 특정 필드만 _source로 추출

curl -X GET "http://localhost:9200/{index_name}/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "_source": ["title", "content"],
  "query": {
    "match_all": {}
  }
}'


⸻

필요하신 쿼리 유형(예: 날짜 필터, bool 쿼리, 정렬 등)이 있으면 예제를 더 드릴 수 있습니다.