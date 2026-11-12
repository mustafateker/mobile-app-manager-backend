from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.modules.apps.dto import to_camel


class CreateMapsJobDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    keywords: list[str] = Field(min_length=1, max_length=50)
    language: str = Field(default="tr", min_length=2, max_length=2)
    depth: int = Field(default=5, ge=1, le=100)
    zoom: int = Field(default=15, ge=1, le=21)
    latitude: float | str | None = Field(default=None)
    longitude: float | str | None = Field(default=None)
    fast_mode: bool = False
    radius: int = Field(default=10_000, ge=1, le=100_000)
    email: bool = False
    extra_reviews: bool = False
    max_time_seconds: int = Field(default=600, ge=60, le=7_200)

    @field_validator("latitude", mode="before")
    @classmethod
    def normalize_latitude(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                return None
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Geçersiz enlem değeri.")
        if not (-90 <= val <= 90):
            raise ValueError("Enlem -90 ile 90 arasında olmalıdır.")
        return val

    @field_validator("longitude", mode="before")
    @classmethod
    def normalize_longitude(cls, value: object) -> float | None:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                return None
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Geçersiz boylam değeri.")
        if not (-180 <= val <= 180):
            raise ValueError("Boylam -180 ile 180 arasında olmalıdır.")
        return val

    @model_validator(mode="after")
    def validate_location(self) -> "CreateMapsJobDto":
        self.keywords = [keyword.strip() for keyword in self.keywords if keyword.strip()]
        if not self.keywords:
            raise ValueError("En az bir arama kelimesi girin.")
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Enlem ve boylam birlikte girilmelidir.")
        if self.fast_mode and self.latitude is None:
            raise ValueError("Hızlı mod için enlem ve boylam gereklidir.")
        return self
