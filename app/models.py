from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Literal




class CreateUserRequest(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=30)]
    password: Annotated[str, Field(..., min_length=6, max_length=50)]
    role: Literal["user", "admin"] = "user"

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, value):
        if " " in value:
            raise ValueError("Username cannot contain spaces")
        return value


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    mode: Annotated[str , Field(default="chat", pattern="^(chat|code|document|image|video)$")]
    


class LoginRequest(BaseModel):
    username: Annotated[str, Field(..., min_length=3, max_length=30)]
    password: Annotated[str, Field(..., min_length=6, max_length=50)]

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, value):
        if " " in value:
            raise ValueError("Username cannot contain spaces")
        return value


