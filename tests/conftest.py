import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "craftbox.settings")
django.setup()
