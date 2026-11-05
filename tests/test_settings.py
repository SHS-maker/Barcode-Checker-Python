import unittest
from dataclasses import asdict

from barcode_checker.settings import AndroidSettingsStore, BOOLEAN_KEYS, Settings


class MemoryPreferences:
    """SharedPreferences boundary test double; no Android dependency required."""
    def __init__(self):
        self.data = {}
        self.pending = {}

    def getBoolean(self, key, default):
        return self.data.get(key, default)

    def getInt(self, key, default):
        return self.data.get(key, default)

    def edit(self):
        self.pending = {}
        return self

    def putBoolean(self, key, value):
        self.pending[key] = value
        return self

    putInt = putBoolean

    def apply(self):
        self.data.update(self.pending)


class SettingsTests(unittest.TestCase):
    def test_original_defaults(self):
        settings = Settings()
        self.assertTrue(all(getattr(settings, key) for key in BOOLEAN_KEYS))
        self.assertEqual(settings.auto_reset_seconds, 0)

    def test_auto_reset_range_and_invalid_input(self):
        settings = Settings()
        for raw, expected in ((-1, 0), (0, 0), (5, 5), (60, 60), (999, 60),
                              ("15", 15), ("", 0), ("bad", 0), (None, 0)):
            settings.set_value("auto_reset_seconds", raw)
            self.assertEqual(settings.auto_reset_seconds, expected)

    def test_unknown_keys_and_wrong_types_rejected(self):
        settings = Settings()
        with self.assertRaises(KeyError):
            settings.set_value("unknown", True)
        with self.assertRaises(TypeError):
            settings.set_value("sound_enabled", "false")

    def test_android_persistence_preserves_all_values(self):
        prefs = MemoryPreferences()
        class Activity:
            def getSharedPreferences(self, name, mode):
                assert name == "barcode_checker_settings" and mode == 0
                return prefs
        store = AndroidSettingsStore(Activity())
        self.assertEqual(store.load(), Settings())
        settings = Settings()
        for key in BOOLEAN_KEYS:
            settings.set_value(key, False)
        settings.set_value("auto_reset_seconds", 42)
        store.save(settings)
        self.assertEqual(asdict(store.load()), asdict(settings))
        self.assertEqual(len(prefs.data), 9)


if __name__ == "__main__":
    unittest.main()
