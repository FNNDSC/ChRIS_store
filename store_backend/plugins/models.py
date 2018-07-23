
from django.db import models
import django_filters
from django.utils import timezone

from rest_framework.filters import FilterSet

from .fields import CPUField, MemoryField


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
    # default resource limits inserted at registration time
    defaults = {
                'min_cpu_limit': 1000,   # in millicores
                'min_memory_limit': 200, # in Mi
                'max_limit': 2147483647  # maxint
               }
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, unique=True)
    dock_image = models.CharField(max_length=500)
    public_repo = models.URLField(max_length=300)
    descriptor_file = models.FileField(max_length=512, upload_to=uploaded_file_path)
    type = models.CharField(choices=PLUGIN_TYPE_CHOICES, default='ds', max_length=4)
    icon = models.URLField(max_length=300, blank=True)
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
    min_gpu_limit = models.IntegerField(null=True, blank=True)
    max_gpu_limit = models.IntegerField(null=True, blank=True)
    min_number_of_workers = models.IntegerField(null=True, blank=True, default=1)
    max_number_of_workers = models.IntegerField(null=True, blank=True,
                                                default=defaults['max_limit'])
    min_cpu_limit = CPUField(null=True, blank=True,
                             default=defaults['min_cpu_limit']) # In millicores
    max_cpu_limit = CPUField(null=True, blank=True,
                             default=defaults['max_limit']) # In millicores
    min_memory_limit = MemoryField(null=True, blank=True,
                                   default=defaults['min_memory_limit']) # In Mi
    max_memory_limit = MemoryField(null=True, blank=True, default=defaults['max_limit'])
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


class PluginFilter(FilterSet):
    min_creation_date = django_filters.DateFilter(name="creation_date", lookup_expr='gte')
    max_creation_date = django_filters.DateFilter(name="creation_date", lookup_expr='lte')
    owner_username = django_filters.CharFilter(name="owner__username", lookup_expr='icontains')
    name = django_filters.CharFilter(name="name", lookup_expr='startswith')
    authors = django_filters.CharFilter(name="authors", lookup_expr='icontains')
    
    class Meta:
        model = Plugin
        fields = ['name', 'dock_image', 'public_repo', 'type', 'category', 'authors',
                  'owner_username', 'min_creation_date', 'max_creation_date', ]


class PluginParameter(models.Model):
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=52)
    action = models.CharField(max_length=20, default='store')
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
    

