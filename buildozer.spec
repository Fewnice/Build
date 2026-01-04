[app]
title = LANVoiceApp
package.name = lanvoiceapp
package.domain = org.local
version = 0.1

# IMPORTANT (سبب الخطأ)
source.dir = .

source.include_exts = py,kv,json

requirements = python3,kivy,websockets,numpy

orientation = portrait

android.permissions = RECORD_AUDIO,INTERNET
android.api = 33
android.minapi = 21
android.arch = arm64-v8a,armeabi-v7a
