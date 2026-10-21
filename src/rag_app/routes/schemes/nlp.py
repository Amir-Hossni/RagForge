from pydantic import BaseModel, HttpUrl, Field, model_validator
from typing import Optional


class PushRequest(BaseModel):
    do_reset: Optional[bool] = False
    
    
class SearchRequest(BaseModel):
    text: str
    limit: Optional[int] = 5    