from app.modules.dashboard.dto import AsoDashboardDto, DashboardDto


class DashboardService:
    def __init__(self, app_service: object, aso_service: object) -> None:
        self.app_service = app_service
        self.aso_service = aso_service

    async def get(self) -> DashboardDto:
        remote_apps: list[object] = []
        connected = False
        if self.aso_service.configured:
            try:
                remote_apps = await self.aso_service.apps()
                connected = True
            except Exception:
                connected = False
        return DashboardDto(
            apps=self.app_service.list(),
            asobeast=AsoDashboardDto(
                configured=self.aso_service.configured,
                connected=connected,
                remote_app_count=len(remote_apps),
            ),
        )

