"""Settings.kt, using the same SharedPreferences keys on Android."""

from dataclasses import dataclass


@dataclass
class Settings:
    show_reset_button: bool = True
    show_manual_entry_button: bool = True
    sound_enabled: bool = True
    vibration_enabled: bool = True
    fullscreen_flash: bool = True
    highlight_differences: bool = True
    tolerance_contains: bool = True
    tolerance_extra_zero: bool = True
    auto_reset_seconds: int = 0

    def set_value(self, key, value):
        if key == "auto_reset_seconds":
            try:
                value = max(0, min(60, int(value)))
            except (ValueError, TypeError, OverflowError):
                value = 0
        elif key in BOOLEAN_KEYS:
            if not isinstance(value, bool):
                raise TypeError("Boolean setting requires bool")
        else:
            raise KeyError(key)
        setattr(self, key, value)


BOOLEAN_KEYS = tuple(key for key in Settings.__dataclass_fields__
                     if key != "auto_reset_seconds")


class AndroidSettingsStore:
    def __init__(self, activity):
        self.prefs = activity.getSharedPreferences("barcode_checker_settings", 0)

    def load(self):
        settings = Settings()
        for key in BOOLEAN_KEYS:
            settings.set_value(key, self.prefs.getBoolean(key, True))
        settings.set_value("auto_reset_seconds", self.prefs.getInt("auto_reset_seconds", 0))
        return settings

    def save(self, settings):
        editor = self.prefs.edit()
        for key in BOOLEAN_KEYS:
            editor.putBoolean(key, getattr(settings, key))
        editor.putInt("auto_reset_seconds", settings.auto_reset_seconds)
        editor.apply()
