from django.apps import AppConfig


class UsersAppConfig(AppConfig):
    name = 'src.users'

    def ready(self):
        pass
