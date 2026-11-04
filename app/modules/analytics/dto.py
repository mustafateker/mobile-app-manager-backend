from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(word.title() for word in tail)


class ScreenViewDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    screen: str
    screen_title: str
    views: int
    unique_visitors: int
    percentage: float


class FunnelStepDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    step_id: str
    title: str
    count: int
    conversion_rate: float
    dropoff_rate: float
    dropoff_count: int


class PaywallAnalysisDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    steps: List[FunnelStepDto]
    dismissed_count: int
    cancelled_count: int
    failed_count: int
    dismiss_reasons: dict[str, int]
    selected_packages: dict[str, int]
    overall_conversion: float


class LiveEventDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    event: str
    event_display: str
    timestamp: str
    screen_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    os: Optional[str] = None
    device_type: Optional[str] = None


class PostHogConfigDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    configured: bool
    connected: bool
    project_id: str
    host: str
    has_api_key: bool


class UpdatePostHogConfigDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    personal_api_key: str
    project_id: Optional[str] = None


class AnalyticsOverviewDto(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    config: PostHogConfigDto
    total_events: int
    active_users: int
    top_screen: str
    screens: List[ScreenViewDto]
    paywall: PaywallAnalysisDto
    recent_events: List[LiveEventDto]
    behavior_summary: str
    time_range: str

