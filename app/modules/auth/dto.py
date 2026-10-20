from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("geçerli bir e-posta girin")
        return value


class UserDto(BaseModel):
    email: str


class SessionDto(BaseModel):
    user: UserDto
