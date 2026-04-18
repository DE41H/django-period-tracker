from django.apps import AppConfig


class CycleConfig(AppConfig):
    name = 'cycle'

    def ready(self) -> None:
        import cycle.signals  # noqa: F401
        return super().ready()
