"""python-for-android entry point. All application behavior is Python."""

import os

# Kivy/SDL supplies the Android runtime. The app uses native Android widgets,
# created through PyJNIus, to preserve scanner focus and Android accessibility.
os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.utils import platform


class BarcodeCheckerApp(App):
    title = "Barcode Checker Python"
    controller = None

    def build(self):
        if platform != "android":
            raise RuntimeError("Diese App ist ausschließlich für Android. Siehe README.md.")
        return Widget()

    def on_start(self):
        from barcode_checker.android_app import AndroidBarcodeChecker
        self.controller = AndroidBarcodeChecker()
        self.controller.start()

    def on_pause(self):
        if self.controller:
            self.controller.pause()
        return True

    def on_resume(self):
        if self.controller:
            self.controller.resume()

    def on_stop(self):
        if self.controller:
            self.controller.stop()


if __name__ == "__main__":
    BarcodeCheckerApp().run()
