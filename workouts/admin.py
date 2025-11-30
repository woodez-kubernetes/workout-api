from django.contrib import admin

# Note: MongoEngine models cannot be used directly with Django admin
# since Django admin is designed for Django ORM models.
# For MongoDB admin interface, consider using:
# 1. Flask-Admin with MongoEngine
# 2. Custom admin views
# 3. Third-party packages like django-mongoengine-admin
#
# For now, we'll use the DRF browsable API as the admin interface.
