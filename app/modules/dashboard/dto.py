from pydantic import BaseModel, ConfigDict

from app.modules.apps.dto import ManagedAppDto


class AsoDashboardDto(BaseModel):
    model_config = ConfigDict(alias_generator=lambda value: {
        "remote_app_count": "remoteAppCount"
    }.get(value, value), populate_by_name=True)

    configured: bool
    connected: bool
    remote_app_count: int


class DashboardDto(BaseModel):
    apps: list[ManagedAppDto]
    asobeast: AsoDashboardDto

