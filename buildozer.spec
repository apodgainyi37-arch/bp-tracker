[app]
title = BP Tracker
package.name = bptracker
package.domain = org.health
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0,fpdf,sqlite3
icon.filename = %(source.dir)s/icon.png
orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
p4a.branch = master
