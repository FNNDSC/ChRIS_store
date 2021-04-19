from django.contrib import admin

# Register your models here.
from .models import PluginMeta,Plugin,PluginParameter

admin.site.register(PluginMeta)
admin.site.register(Plugin)
admin.site.register(PluginParameter)
