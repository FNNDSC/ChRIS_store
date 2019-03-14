
from django.db import models
from django.utils import timezone

import django_filters
from django_filters.rest_framework import FilterSet

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
    # SWIFT_CONTAINER_NAME/<original_owner_username>/uploads/<today_path>/<filename>
    owner = instance.owner.all()[0]
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
    name = models.CharField(max_length=100)
    dock_image = models.CharField(max_length=500)
    public_repo = models.URLField(max_length=300)
    descriptor_file = models.FileField(max_length=512, upload_to=uploaded_file_path)
    version = models.CharField(max_length=10)
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
    owner = models.ManyToManyField('auth.User', related_name='plugin')

    class Meta:
        unique_together = ('name', 'version',)
        ordering = ('type',)

    def __str__(self):
        return self.name

    def get_plugin_parameter_names(self):
        """
        Custom method to get the list of plugin parameter names.
        """
        params = self.parameters.all()
        return [param.name for param in params]

    def add_owner(self, new_owner):
        """
        Custom method to add a new owner to the plugin.
        """
        owners = [o for o in self.owner.all()]
        if new_owner not in owners:
            owners.append(new_owner)
            # update list of owners for all plugins with same name
            plg_list = Plugin.objects.filter(name=self.name)
            for plg in plg_list:
                plg.owner.set(owners)
                plg.modification_date = timezone.now()
                plg.save()


class PluginFilter(FilterSet):
    min_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='gte')
    max_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='lte')
    owner_username = django_filters.CharFilter(field_name='owner__username',
                                               lookup_expr='icontains')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    name_exact = django_filters.CharFilter(field_name='name', lookup_expr='exact')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category', lookup_expr='icontains')
    description = django_filters.CharFilter(field_name='description',
                                            lookup_expr='icontains')
    authors = django_filters.CharFilter(field_name='authors', lookup_expr='icontains')
    name_title_category = django_filters.CharFilter(method='search_name_title_category')
    name_latest = django_filters.CharFilter(method='search_latest')
    name_exact_latest = django_filters.CharFilter(method='search_latest')

    def search_name_title_category(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with all plugins for which name or title
        or category matches the search value.
        """
        # construct the full lookup expression.
        lookup = models.Q(name__icontains=value) | models.Q(title__icontains=value)
        lookup = lookup | models.Q(category__icontains=value)
        return queryset.filter(lookup)

    def search_latest(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with the latest version according to
        creation date of all plugins whose name matches the search value.
        """
        if name == 'name_exact_latest':
            return queryset.filter(name=value).order_by('-creation_date')[:1]
        else:
            qs = queryset.filter(name__icontains=value).order_by('name', '-creation_date')
            result_id_list = []
            plg_name = ''
            for plg in qs:
                if plg.name != plg_name:
                    result_id_list.append(plg.id)
                    plg_name = plg.name
            return qs.filter(pk__in=result_id_list)
    
    class Meta:
        model = Plugin
        fields = ['id', 'name', 'name_latest', 'name_exact', 'name_exact_latest',
                  'dock_image', 'public_repo', 'type', 'category', 'authors',
                  'owner_username', 'min_creation_date', 'max_creation_date', 'title',
                  'version', 'description', 'name_title_category']


class PluginParameter(models.Model):
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=52)
    action = models.CharField(max_length=20, default='store')
    optional = models.BooleanField(default=True)
    type = models.CharField(choices=TYPE_CHOICES, default='string', max_length=10)
    help = models.TextField(blank=True)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE,
                               related_name='parameters')
    
    class Meta:
        ordering = ('plugin',)

    def __str__(self):
        return self.name


class DefaultStringParameter(models.Model):
    value = models.CharField(max_length=200, blank=True)
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='string_default')

    def __str__(self):
        return self.value


class DefaultIntParameter(models.Model):
    value = models.IntegerField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='integer_default')

    def __str__(self):
        return str(self.value)


class DefaultFloatParameter(models.Model):
    value = models.FloatField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='float_default')

    def __str__(self):
        return str(self.value)


class DefaultBoolParameter(models.Model):
    value = models.BooleanField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='boolean_default')

    def __str__(self):
        return str(self.value)


class DefaultPathParameter(models.Model):
    value = models.CharField(max_length=200, blank=True)
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='path_default')

    def __str__(self):
        return self.value
