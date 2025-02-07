
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class MapDataUtilParser(BaseModel):
    getter: str = Field(description="MapDataUtil getter")
    setter: str = Field(description="MapDataUtil setter")

# PydanticOutputParser 생성
map_data_util_parser = PydanticOutputParser(pydantic_object=MapDataUtilParser)