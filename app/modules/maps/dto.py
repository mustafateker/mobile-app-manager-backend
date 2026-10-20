from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.apps.dto import to_camel


class CreateMapsJobDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    keywords: list[str] = Field(min_length=1, max_length=50)
    language: str = Field(default="tr", min_length=2, max_length=2)
    depth: int = Field(default=5, ge=1, le=100)
    zoom: int = Field(default=15, ge=1, le=21)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    fast_mode: bool = False
    radius: int = Field(default=10_000, ge=1, le=100_000)
    email: bool = False
    extra_reviews: bool = False
    max_time_seconds: int = Field(default=600, ge=60, le=7_200)

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
