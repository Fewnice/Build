[app]
title = LANVoiceApp
package.name = lanvoiceapp
package.domain = org.local
source.include_exts = py,json
version = 0.1
orientation = portrait

# ضع هنا المتطلبات التي استخدمناها
requirements = python3,kivy,fastapi,uvicorn,sounddevice,numpy,websockets

# أيقونة (اختياري)
# icon.filename = %(source.dir)s/data/icon.png

# Android permissions
android.permissions = RECORD_AUDIO,INTERNET
