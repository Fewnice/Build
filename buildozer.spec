[app]
# معلومات أساسية
title = LANVoiceApp
package.name = lanvoiceapp
package.domain = org.local
version = 0.1
orientation = portrait

# مكان مصدر الكود (مهم)
source.dir = .

# امتدادات الملفات المسموح تضمينها
source.include_exts = py,kv,json

# المتطلبات الأساسية (مبسطة لمرحلة البناء الأولى)
requirements = python3,kivy,websockets,numpy

# صلاحيات أندرويد المطلوبة
android.permissions = RECORD_AUDIO,INTERNET

# إعدادات أندرويد مبسطة
android.api = 33
android.minapi = 21
android.arch = armeabi-v7a,arm64-v8a
