from pydantic import ConfigDict, BaseModel , Field, validator
from typing import  Optional
from bson.objectid import ObjectId

class Project(BaseModel):

    id: Optional[ObjectId] = Field(default=None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @validator("project_id")
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError("project_id must alphanumeric string")
        return value

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )