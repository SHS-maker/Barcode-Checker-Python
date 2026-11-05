"""Native Android UI and device feedback, translated from the three Activities.

This module is loaded only on Android. Java interfaces are implemented in Python;
there are no Kotlin/Java application sources or manufacturer SDK dependencies.
All native widget access runs on Android's UI thread.
"""

import logging

from android.runnable import run_on_ui_thread
from jnius import PythonJavaClass, autoclass, cast, java_method

from .core import ScanSession, ScanState, differing_indices, highlight_ranges
from .settings import AndroidSettingsStore

log = logging.getLogger(__name__)
JString = autoclass("java.lang.String")
Color = autoclass("android.graphics.Color")
LinearLayout = autoclass("android.widget.LinearLayout")
LayoutParams = autoclass("android.widget.LinearLayout$LayoutParams")
TextView = autoclass("android.widget.TextView")
Button = autoclass("android.widget.Button")
EditText = autoclass("android.widget.EditText")
Switch = autoclass("android.widget.Switch")
ScrollView = autoclass("android.widget.ScrollView")
GradientDrawable = autoclass("android.graphics.drawable.GradientDrawable")
AlertBuilder = autoclass("android.app.AlertDialog$Builder")
BuildVersion = autoclass("android.os.Build$VERSION")
KeyEvent = autoclass("android.view.KeyEvent")

BACKGROUND = "#000000"
FIELD = "#1C1C1C"
BORDER = "#2E2E2E"
WHITE = "#FFFFFF"
MUTED = "#808080"
GREEN = "#00C853"
RED = "#FF1744"


class Click(PythonJavaClass):
    __javainterfaces__ = ["android/view/View$OnClickListener"]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("(Landroid/view/View;)V")
    def onClick(self, view):
        self.callback()


class DialogClick(PythonJavaClass):
    __javainterfaces__ = ["android/content/DialogInterface$OnClickListener"]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("(Landroid/content/DialogInterface;I)V")
    def onClick(self, dialog, which):
        self.callback()


class Dismiss(PythonJavaClass):
    __javainterfaces__ = ["android/content/DialogInterface$OnDismissListener"]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("(Landroid/content/DialogInterface;)V")
    def onDismiss(self, dialog):
        self.callback()


class Checked(PythonJavaClass):
    __javainterfaces__ = ["android/widget/CompoundButton$OnCheckedChangeListener"]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("(Landroid/widget/CompoundButton;Z)V")
    def onCheckedChanged(self, button, checked):
        self.callback(bool(checked))


class Runnable(PythonJavaClass):
    __javainterfaces__ = ["java/lang/Runnable"]

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    @java_method("()V")
    def run(self):
        self.callback()


class ScannerKeys(PythonJavaClass):
    __javainterfaces__ = ["android/view/View$OnKeyListener"]

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @java_method("(Landroid/view/View;ILandroid/view/KeyEvent;)Z")
    def onKey(self, view, code, event):
        if code in (KeyEvent.KEYCODE_ENTER, KeyEvent.KEYCODE_NUMPAD_ENTER):
            if event.getAction() == KeyEvent.ACTION_DOWN:
                self.controller.consume(str(self.controller.scanner.getText().toString()))
            return True
        return False


class ScannerText(PythonJavaClass):
    __javainterfaces__ = ["android/text/TextWatcher"]

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @java_method("(Ljava/lang/CharSequence;III)V")
    def beforeTextChanged(self, text, start, count, after):
        pass

    @java_method("(Ljava/lang/CharSequence;III)V")
    def onTextChanged(self, text, start, before, count):
        pass

    @java_method("(Landroid/text/Editable;)V")
    def afterTextChanged(self, editable):
        text = str(editable.toString())
        if "\r" in text or "\n" in text:
            self.controller.consume(text)


class WindowFocus(PythonJavaClass):
    __javainterfaces__ = ["android/view/ViewTreeObserver$OnWindowFocusChangeListener"]

    def __init__(self, controller):
        super().__init__()
        self.controller = controller

    @java_method("(Z)V")
    def onWindowFocusChanged(self, focused):
        if focused:
            self.controller.focus_scanner()


class AndroidBarcodeChecker:
    def __init__(self):
        self.activity = autoclass("org.kivy.android.PythonActivity").mActivity
        self.session = ScanSession()
        self.store = AndroidSettingsStore(self.activity)
        self.settings = self.store.load()
        self.handler = autoclass("android.os.Handler")(
            autoclass("android.os.Looper").getMainLooper())
        self.reset_task = Runnable(self.reset)
        self.listeners = []  # Java proxies must remain alive while Java uses them.
        self.dialog_refs = []
        self.dialog = None
        self.auto_reset_input = None
        self.tone = None
        self.vibrator = None
        self.root = None
        self.stopped = False

    def dp(self, value):
        density = self.activity.getResources().getDisplayMetrics().density
        return round(value * density)

    def background(self, view, fill=FIELD):
        shape = GradientDrawable()
        shape.setColor(Color.parseColor(fill))
        shape.setCornerRadius(float(self.dp(8)))
        shape.setStroke(self.dp(1), Color.parseColor(BORDER))
        view.setBackground(shape)

    def text(self, value="", size=16, color=WHITE, bold=False):
        view = TextView(self.activity)
        view.setText(JString(value))
        view.setTextSize(float(size))
        view.setTextColor(Color.parseColor(color))
        view.setGravity(17)
        view.setPadding(self.dp(10), self.dp(8), self.dp(10), self.dp(8))
        if bold:
            view.setTypeface(None, 1)
        return view

    def button(self, title, callback, refs=None):
        view = Button(self.activity)
        view.setText(JString(title))
        view.setTextColor(Color.parseColor(WHITE))
        view.setTextSize(16.0)
        view.setAllCaps(False)
        self.background(view)
        listener = Click(callback)
        (self.listeners if refs is None else refs).append(listener)
        view.setOnClickListener(listener)
        return view

    def fullscreen(self):
        window = self.activity.getWindow()
        window.setSoftInputMode(3 | 48)  # ALWAYS_HIDDEN | ADJUST_NOTHING
        if BuildVersion.SDK_INT >= 30:
            window.setDecorFitsSystemWindows(False)
            controller = window.getInsetsController()
            if controller:
                controller.hide(autoclass("android.view.WindowInsets$Type").systemBars())
                controller.setSystemBarsBehavior(2)
        else:
            window.getDecorView().setSystemUiVisibility(5894)

    def focus_scanner(self):
        if self.stopped or self.dialog is not None:
            return
        self.scanner.requestFocus()
        manager = cast("android.view.inputmethod.InputMethodManager",
                       self.activity.getSystemService(JString("input_method")))
        manager.hideSoftInputFromWindow(self.scanner.getWindowToken(), 0)
        self.fullscreen()

    @run_on_ui_thread
    def start(self):
        self.root = LinearLayout(self.activity)
        self.root.setOrientation(1)
        self.root.setPadding(self.dp(16), self.dp(16), self.dp(16), self.dp(16))
        self.root.setBackgroundColor(Color.parseColor(BACKGROUND))
        self.root.setFocusableInTouchMode(True)

        header = LinearLayout(self.activity)
        title = self.text("BARCODE CHECKER", 13, MUTED)
        header.addView(title, LayoutParams(0, self.dp(44), 1.0))
        settings_button = self.button("⚙", self.open_settings)
        settings_button.setContentDescription(JString("Einstellungen öffnen"))
        header.addView(settings_button, LayoutParams(self.dp(48), self.dp(44)))
        self.root.addView(header, LayoutParams(-1, self.dp(52)))

        self.barcode_views = []
        for title in ("BARCODE 1", "BARCODE 2"):
            label = self.text(title, 13, MUTED)
            label.setGravity(3 | 16)
            self.root.addView(label, LayoutParams(-1, self.dp(28)))
            value = self.text("Scan…", 20)
            value.setMaxLines(3)
            value.setAutoSizeTextTypeUniformWithConfiguration(11, 20, 1, 2)
            self.background(value)
            params = LayoutParams(-1, 0, 1.0)
            params.bottomMargin = self.dp(10)
            self.root.addView(value, params)
            self.barcode_views.append(value)

        self.result_view = self.text("", 30, bold=True)
        self.background(self.result_view)
        self.root.addView(self.result_view, LayoutParams(-1, 0, 1.5))
        self.reset_button = self.button("RESET", self.reset)
        self.manual_button = self.button("Manuelle Eingabe", self.open_manual)
        for button, height in ((self.reset_button, 56), (self.manual_button, 44)):
            params = LayoutParams(-1, self.dp(height))
            params.topMargin = self.dp(10)
            self.root.addView(button, params)

        self.scanner = EditText(self.activity)
        self.scanner.setInputType(1 | 0x80000)
        self.scanner.setMaxLines(1)
        self.scanner.setShowSoftInputOnFocus(False)
        self.scanner.setCursorVisible(False)
        self.scanner.setAlpha(0.0)
        self.scanner.setImportantForAccessibility(2)
        keys, watcher = ScannerKeys(self), ScannerText(self)
        self.listeners.extend((keys, watcher))
        self.scanner.setOnKeyListener(keys)
        self.scanner.addTextChangedListener(watcher)
        self.root.addView(self.scanner, LayoutParams(1, 1))
        root_click = Click(self.focus_scanner)
        self.listeners.append(root_click)
        self.root.setOnClickListener(root_click)
        # Overlay SDL instead of replacing its surface; its event loop stays alive.
        self.activity.addContentView(self.root, autoclass(
            "android.view.ViewGroup$LayoutParams")(-1, -1))
        self.window_focus = WindowFocus(self)
        self.listeners.append(self.window_focus)
        self.root.getViewTreeObserver().addOnWindowFocusChangeListener(self.window_focus)
        try:
            self.tone = autoclass("android.media.ToneGenerator")(5, 100)
        except Exception:
            log.exception("Signaltöne sind auf diesem Gerät nicht verfügbar")
        try:
            if BuildVersion.SDK_INT >= 31:
                manager = cast("android.os.VibratorManager", self.activity.getSystemService(
                    JString("vibrator_manager")))
                self.vibrator = manager.getDefaultVibrator()
            else:
                self.vibrator = cast("android.os.Vibrator",
                                     self.activity.getSystemService(JString("vibrator")))
        except Exception:
            log.exception("Vibration ist auf diesem Gerät nicht verfügbar")
        self.apply_settings()
        self.reset()

    def apply_settings(self):
        self.reset_button.setVisibility(0 if self.settings.show_reset_button else 8)
        self.manual_button.setVisibility(0 if self.settings.show_manual_entry_button else 8)

    def reset(self):
        self.handler.removeCallbacks(self.reset_task)
        self.session.reset()
        if self.dialog is not None and self.auto_reset_input is None:
            self.dialog.dismiss()
        for view in self.barcode_views:
            view.setText(JString("Scan…"))
        self.result_view.setText(JString(""))
        self.background(self.result_view)
        self.root.setBackgroundColor(Color.parseColor(BACKGROUND))
        self.scanner.setText(JString(""))
        self.focus_scanner()

    def consume(self, raw):
        self.scanner.setText(JString(""))
        result = self.session.consume(raw, self.settings)
        if self.session.barcode1 is not None and result is None:
            # Do not remove highlighting when additional scans are ignored.
            if self.session.state is ScanState.WAITING_BARCODE2:
                self.barcode_views[0].setText(JString(self.session.barcode1))
        if result is None:
            return
        self.barcode_views[0].setText(JString(result.first))
        self.barcode_views[1].setText(JString(result.second))
        if not result.match and self.settings.highlight_differences:
            diffs = differing_indices(result.first, result.second)
            for view, code, diff in zip(self.barcode_views,
                                         (result.first, result.second), diffs):
                view.setText(self.highlight(code, diff))
        self.show_result(result.match)
        if self.settings.auto_reset_seconds > 0:
            self.handler.postDelayed(self.reset_task, self.settings.auto_reset_seconds * 1000)

    def highlight(self, code, indices):
        text = autoclass("android.text.SpannableString")(JString(code))
        for start, end in highlight_ranges(code, indices):
            for span in (
                autoclass("android.text.style.BackgroundColorSpan")(Color.parseColor(RED)),
                autoclass("android.text.style.ForegroundColorSpan")(Color.parseColor(WHITE)),
                autoclass("android.text.style.StyleSpan")(1),
            ):
                text.setSpan(span, start, end, 33)
        return text

    def show_result(self, match):
        color = GREEN if match else RED
        self.result_view.setText(JString("CORRECT" if match else "INCORRECT"))
        self.background(self.result_view, color)
        if self.settings.fullscreen_flash:
            self.root.setBackgroundColor(Color.parseColor(color))
        if self.settings.sound_enabled and self.tone is not None:
            try:
                generator = autoclass("android.media.ToneGenerator")
                self.tone.startTone(generator.TONE_PROP_ACK if match
                                    else generator.TONE_PROP_NACK, 200 if match else 400)
            except Exception:
                log.exception("Signalton konnte nicht abgespielt werden")
        if self.settings.vibration_enabled and self.vibrator is not None:
            try:
                if self.vibrator.hasVibrator():
                    effect = autoclass("android.os.VibrationEffect")
                    self.vibrator.vibrate(effect.createOneShot(120, -1) if match
                                          else effect.createWaveform([0, 150, 100, 150], -1))
            except Exception:
                log.exception("Vibration konnte nicht ausgelöst werden")

    def modal_dismissed(self):
        if self.auto_reset_input is not None:
            self.save_auto_reset()
        self.auto_reset_input = None
        self.dialog = None
        self.apply_settings()
        self.focus_scanner()

    def open_manual(self):
        if self.session.state is ScanState.SHOWING_RESULT or self.dialog is not None:
            return
        self.scanner.setText(JString(""))
        self.scanner.clearFocus()
        field = EditText(self.activity)
        field.setInputType(1)
        field.setHint(JString("Barcode"))
        first = self.session.state is ScanState.WAITING_BARCODE1
        confirm = DialogClick(lambda: self.consume(str(field.getText().toString())))
        cancel = DialogClick(lambda: None)
        dismiss = Dismiss(self.modal_dismissed)
        self.dialog_refs = [field, confirm, cancel, dismiss]
        self.dialog = (AlertBuilder(self.activity)
                       .setTitle(JString("Barcode 1 eingeben" if first else "Barcode 2 eingeben"))
                       .setView(field)
                       .setPositiveButton(JString("OK"), confirm)
                       .setNegativeButton(JString("Abbrechen"), cancel).create())
        self.dialog.setOnDismissListener(dismiss)
        self.dialog.show()
        field.requestFocus()
        self.dialog.getWindow().setSoftInputMode(5)

    def save_auto_reset(self):
        if self.auto_reset_input is not None:
            self.settings.set_value("auto_reset_seconds",
                                    str(self.auto_reset_input.getText().toString()))
            self.store.save(self.settings)

    def open_settings(self):
        if self.dialog is not None:
            return
        self.scanner.setText(JString(""))
        self.scanner.clearFocus()
        self.dialog_refs = []
        content = LinearLayout(self.activity)
        content.setOrientation(1)
        content.setPadding(self.dp(16), self.dp(8), self.dp(16), self.dp(16))
        content.setBackgroundColor(Color.parseColor(BACKGROUND))
        groups = (
            ("Knöpfe", (
                ("show_reset_button", "RESET-Knopf anzeigen", ""),
                ("show_manual_entry_button", "Knopf „Manuelle Eingabe“ anzeigen", ""))),
            ("Rückmeldung", (
                ("sound_enabled", "Signaltöne abspielen", ""),
                ("vibration_enabled", "Vibration", "CORRECT: einmal kurz · INCORRECT: zweimal kurz"),
                ("fullscreen_flash", "Ganzen Bildschirm einfärben", "Aus: nur das Ergebnisfeld leuchtet grün bzw. rot"),
                ("highlight_differences", "Abweichende Zeichen markieren", "Bei INCORRECT abweichende Zeichen rot hervorheben"))),
            ("Vergleich", (
                ("tolerance_contains", "Teil-Übereinstimmung erlauben", "Ein Barcode ist vollständig im anderen enthalten"),
                ("tolerance_extra_zero", "Eine zusätzliche „0“ ignorieren", "Die Codes unterscheiden sich nur um eine einzelne 0"))),
        )
        for group, options in groups:
            content.addView(self.text(group.upper(), 13, MUTED), LayoutParams(-1, self.dp(40)))
            for key, title, hint in options:
                row = LinearLayout(self.activity)
                row.setGravity(16)
                labels = LinearLayout(self.activity)
                labels.setOrientation(1)
                label = self.text(title, 15)
                label.setGravity(3 | 16)
                labels.addView(label, LayoutParams(-1, -2))
                if hint:
                    description = self.text(hint, 12, MUTED)
                    description.setGravity(3 | 16)
                    labels.addView(description, LayoutParams(-1, -2))
                row.addView(labels, LayoutParams(0, -2, 1.0))
                switch = Switch(self.activity)
                switch.setContentDescription(JString(title))
                switch.setChecked(getattr(self.settings, key))
                def update(value, setting_key=key):
                    self.settings.set_value(setting_key, value)
                    self.store.save(self.settings)
                listener = Checked(update)
                self.dialog_refs.append(listener)
                switch.setOnCheckedChangeListener(listener)
                row.addView(switch, LayoutParams(-2, -2))
                content.addView(row, LayoutParams(-1, -2))
        content.addView(self.text("AUTOMATISCHER RESET", 13, MUTED), LayoutParams(-1, self.dp(40)))
        content.addView(self.text("Sekunden nach dem Ergebnis. 0 = aus (nur per RESET-Knopf)", 13, MUTED),
                        LayoutParams(-1, -2))
        self.auto_reset_input = EditText(self.activity)
        self.auto_reset_input.setInputType(2)
        self.auto_reset_input.setTextColor(Color.parseColor(WHITE))
        self.auto_reset_input.setHintTextColor(Color.parseColor(MUTED))
        self.auto_reset_input.setHint(JString("Sek. (0–60)"))
        if self.settings.auto_reset_seconds:
            self.auto_reset_input.setText(JString(str(self.settings.auto_reset_seconds)))
        content.addView(self.auto_reset_input, LayoutParams(-1, -2))
        scroll = ScrollView(self.activity)
        scroll.addView(content)
        done = DialogClick(self.save_auto_reset)
        dismiss = Dismiss(self.modal_dismissed)
        self.dialog_refs.extend((done, dismiss, scroll, content, self.auto_reset_input))
        self.dialog = (AlertBuilder(self.activity).setTitle(JString("Einstellungen"))
                       .setView(scroll).setPositiveButton(JString("FERTIG"), done).create())
        self.dialog.setOnDismissListener(dismiss)
        self.dialog.show()
        self.dialog.getWindow().setSoftInputMode(3)

    @run_on_ui_thread
    def pause(self):
        self.save_auto_reset()

    @run_on_ui_thread
    def resume(self):
        if self.root is not None and not self.stopped:
            self.apply_settings()
            self.focus_scanner()

    @run_on_ui_thread
    def stop(self):
        self.stopped = True
        self.handler.removeCallbacks(self.reset_task)
        if self.dialog is not None:
            self.dialog.dismiss()
        if self.tone is not None:
            self.tone.release()
            self.tone = None
        if self.vibrator is not None:
            self.vibrator.cancel()
        if self.root is not None:
            observer = self.root.getViewTreeObserver()
            if observer.isAlive():
                observer.removeOnWindowFocusChangeListener(self.window_focus)
            parent = self.root.getParent()
            if parent is not None:
                cast("android.view.ViewGroup", parent).removeView(self.root)
