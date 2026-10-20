from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Optional
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(word.title() for word in tail)


def empty_to_none(value: object) -> object:
    return None if value == "" else value


def validate_nullable_text(value: Optional[str]) -> Optional[str]:
    if value is not None and len(value) > 200:
        raise ValueError("metin en fazla 200 karakter olabilir")
    return value


NullableText = Annotated[
    Optional[str], BeforeValidator(empty_to_none), AfterValidator(validate_nullable_text)
]
NullableUrl = Annotated[Optional[HttpUrl], BeforeValidator(empty_to_none)]


class AppStatus(str, Enum):
    DEVELOPMENT = "development"
    REVIEW = "review"
    LIVE = "live"


class AppBaseDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    slug: str
    ios_bundle_id: NullableText = None
    android_package: NullableText = None
    app_store_url: NullableUrl = None
    play_store_url: NullableUrl = None
    asobeast_app_id: NullableText = None
    color: str = "#2563eb"
    status: AppStatus = AppStatus.DEVELOPMENT

    @field_validator("name", "slug", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9-]+", value):
            raise ValueError("slug yalnızca küçük harf, rakam ve tire içerebilir")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("color #RRGGBB biçiminde olmalıdır")
        return value


class CreateAppDto(AppBaseDto):
    pass


class UpdateAppDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=80)
    slug: str | None = None
    ios_bundle_id: NullableText = None
    android_package: NullableText = None
    app_store_url: NullableUrl = None
    play_store_url: NullableUrl = None
    asobeast_app_id: NullableText = None
    color: str | None = None
    status: AppStatus | None = None

    @field_validator("name", "slug", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[a-z0-9-]+", value):
            raise ValueError("slug yalnızca küçük harf, rakam ve tire içerebilir")
        return value

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("color #RRGGBB biçiminde olmalıdır")
        return value


class ManagedAppDto(AppBaseDto):
    id: UUID
    created_at: datetime
    updated_at: datetime
