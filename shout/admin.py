from django.contrib import admin
from shout import models


@admin.register(models.Shout)
class ShoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'from_user', 'audience', 'subject', 'body')
