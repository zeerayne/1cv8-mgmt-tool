import importlib
import os

from conf import default_settings, global_settings


SETTINGS_ENVIRONMENT_VARIABLE = '1CV8MGMT_SETTINGS_MODULE'


class Settings:
    def __init__(self):
        # update this dict from global and default settings (but only for ALL_CAPS settings)
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))

        for setting in dir(default_settings):
            if setting.isupper():
                setattr(self, setting, getattr(default_settings, setting))

        # store the settings module in case someone later cares
        self.SETTINGS_MODULE = os.environ.get(SETTINGS_ENVIRONMENT_VARIABLE, 'settings')
        self._explicit_settings = set()

        mod = importlib.import_module(self.SETTINGS_MODULE)
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)

                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

    def is_overridden(self, setting):
        return setting in self._explicit_settings

    def __repr__(self):
        return '<%(cls)s "%(settings_module)s">' % {
            "cls": self.__class__.__name__,
            "settings_module": self.SETTINGS_MODULE,
        }


settings = Settings()
