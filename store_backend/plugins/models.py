
import json
import swiftclient

from django.db import models
import django_filters
from django.conf import settings
from django.utils import timezone

from rest_framework.filters import FilterSet


# API types
TYPE_CHOICES = [("string", "String values"), ("float", "Float values"),
                ("boolean", "Boolean values"), ("integer", "Integer values"),
                ("path", "Path values")]

# table of equivalence between front-end types and back-end types
TYPES = {'string': 'str', 'integer': 'int', 'float': 'float', 'boolean': 'bool',
         'path': 'path'}

PLUGIN_TYPE_CHOICES = [("ds", "Data plugin"), ("fs", "Filesystem plugin")]


def uploaded_file_path(instance, filename):
    # file will be stored to Swift at:
    # SWIFT_CONTAINER_NAME/<username>/<uploads>/<today_path>/<filename>
    owner = instance.owner
    username = owner.username
    today = timezone.now()
    today_path = today.strftime("%Y/%m/%d/%H/%M")
    return '{0}/{1}/{2}/{3}'.format(username, 'uploads', today_path, filename)


class Plugin(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, unique=True)
    dock_image = models.CharField(max_length=500)
    public_repo = models.URLField(max_length=300)
    descriptor_file = models.FileField(max_length=512, upload_to=uploaded_file_path)
    type = models.CharField(choices=PLUGIN_TYPE_CHOICES, default='ds', max_length=4)
    execshell = models.CharField(max_length=50, blank=True)
    selfpath = models.CharField(max_length=512, blank=True)
    selfexec = models.CharField(max_length=50, blank=True)
    authors = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=400, blank=True)
    category = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=800, blank=True)
    documentation = models.CharField(max_length=800, blank=True)
    license = models.CharField(max_length=50, blank=True)
    version = models.CharField(max_length=10, blank=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                               related_name='plugin')

    class Meta:
        ordering = ('type',)

    def __str__(self):
        return self.name

    def get_plugin_parameter_names(self):
        """
        Custom method to get the list of plugin parameter names.
        """
        params = self.parameters.all()
        return [param.name for param in params]

    def read_descriptor_file(self):
        """
        Custom method to read the plugin representation from the JSON decriptor file.
        """
        # initiate a Swift service connection
        conn = swiftclient.Connection(
            user=settings.SWIFT_USERNAME,
            key=settings.SWIFT_KEY,
            authurl=settings.SWIFT_AUTH_URL,
        )
        fpath = self.descriptor_file.name
        obj_tuple = conn.get_object(settings.SWIFT_CONTAINER_NAME, fpath)
        json_repr = json.loads(obj_tuple[1].decode())
        return json_repr

    def save_descriptors(self, app_reprentation):
        """
        Custom method to save the plugin's app representation descriptors into the DB.
        """
        self.type = app_reprentation['type']
        self.authors = app_reprentation['authors']
        self.title = app_reprentation['title']
        self.description = app_reprentation['description']
        self.license = app_reprentation['license']
        self.version = app_reprentation['version']
        self.execshell = app_reprentation['execshell']
        self.selfpath = app_reprentation['selfpath']
        self.selfexec = app_reprentation['selfexec']
        if 'category' in app_reprentation:
            self.category = app_reprentation['category']
        if 'documentation' in app_reprentation:
            self.documentation = app_reprentation['documentation']
        self.save()
        # delete plugin's parameters from the db
        if self.parameters:
            self.parameters.all().delete()
        # save new plugin's parameters to the db
        params = app_reprentation['parameters']
        for param in params:
            self._save_plugin_param(param)

    def _save_plugin_param(self, parameter):
        """
        Internal method to save a plugin's parameter into the DB.
        """
        # save plugin parameter to the db
        plugin_param = PluginParameter()
        param_type = [key for key in TYPES if TYPES[key] == parameter['type']][0]
        param_default = ""
        if parameter['default']:
            param_default = str(parameter['default'])
        plugin_param.plugin = self
        plugin_param.name = parameter['name']
        plugin_param.type = param_type
        plugin_param.optional = parameter['optional']
        plugin_param.default = param_default
        plugin_param.help = parameter['help']
        plugin_param.save()


class PluginFilter(FilterSet):
    min_creation_date = django_filters.DateFilter(name="creation_date", lookup_expr='gte')
    max_creation_date = django_filters.DateFilter(name="creation_date", lookup_expr='lte')
    
    class Meta:
        model = Plugin
        fields = ['name', 'dock_image', 'public_repo', 'type', 'category', 'owner',
                  'min_creation_date', 'max_creation_date', ]


class PluginParameter(models.Model):
    name = models.CharField(max_length=100)
    optional = models.BooleanField(default=True)
    default = models.CharField(max_length=200, blank=True)
    type = models.CharField(choices=TYPE_CHOICES, default='string', max_length=10)
    help = models.TextField(blank=True)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE,
                               related_name='parameters')
    
    class Meta:
        ordering = ('plugin',)

    def __str__(self):
        return self.name
    

