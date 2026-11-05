[app]
title = Barcode Checker Python
package.name = barcodecheckerpython
package.domain = com.melber
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = tests,docs,.git,.github,.venv,venv,bin,__pycache__
version = 1.0.0
requirements = python3,kivy==2.3.1,pyjnius==1.7.0,android
orientation = portrait
fullscreen = 1
android.permissions = VIBRATE
android.api = 34
android.minapi = 26
android.ndk = 28c
android.ndk_api = 26
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = False
android.debug_artifact = apk
android.release_artifact = apk
android.presplash_color = #000000
p4a.bootstrap = sdl2
p4a.branch = v2026.05.09

[buildozer]
log_level = 2
warn_on_root = 1
