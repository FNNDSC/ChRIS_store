
from django.db import models
from django.utils import timezone

import django_filters
from django_filters.rest_framework import FilterSet

from .fields import CPUField, MemoryField

# API types
TYPE_CHOICES = [("string", "String values"), ("float", "Float values"),
                ("boolean", "Boolean values"), ("integer", "Integer values"),
                ("path", "Path values"), ("unextpath", "Unextracted path values")]

# table of equivalence between front-end types and back-end types
TYPES = {'string': 'str', 'integer': 'int', 'float': 'float', 'boolean': 'bool',
         'path': 'path', 'unextpath': 'unextpath'}

PLUGIN_TYPE_CHOICES = [("ds", "Data plugin"), ("fs", "Filesystem plugin")]


class PluginMeta(models.Model):
    """
    Model class that defines the meta info for a plugin that is the same across
    plugin's versions. If a user owns and/or is a fan of a plugin's meta then he/she
    owns and/or is a fan of all the plugin's versions.
    """
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=400, blank=True)
    public_repo = models.URLField(max_length=300)
    license = models.CharField(max_length=50, blank=True)
    type = models.CharField(choices=PLUGIN_TYPE_CHOICES, default='ds', max_length=4)
    icon = models.URLField(max_length=300, blank=True)
    category = models.CharField(max_length=100, blank=True)
    authors = models.CharField(max_length=200, blank=True)
    documentation = models.CharField(max_length=800, blank=True)
    fan = models.ManyToManyField('auth.User', related_name='favorite_plugin_metas',
                                 through='PluginMetaStar')
    owner = models.ManyToManyField('auth.User', related_name='owned_plugin_metas')

    class Meta:
        ordering = ('type', '-creation_date',)

    def __str__(self):
        return str(self.name)

    def add_owner(self, new_owner):
        """
        Custom method to add a new owner to the plugin.
        """
        self.owner.add(new_owner)


class PluginMetaFilter(FilterSet):
    """
    Filter class for the PluginMeta model.
    """
    min_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='gte')
    max_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='lte')
    owner_username = django_filters.CharFilter(field_name='owner__username',
                                               lookup_expr='exact')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    name_exact = django_filters.CharFilter(field_name='name', lookup_expr='exact')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category', lookup_expr='icontains')
    type = django_filters.CharFilter(field_name='type', lookup_expr='exact')
    authors = django_filters.CharFilter(field_name='authors', lookup_expr='icontains')
    name_title_category = django_filters.CharFilter(method='search_name_title_category')
    name_authors_category = django_filters.CharFilter(
        method='search_name_authors_category')

    def search_name_title_category(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with all plugins for which name or title
        or category matches the search value.
        """
        # construct the full lookup expression.
        lookup = models.Q(name__icontains=value)
        lookup = lookup | models.Q(title__icontains=value)
        lookup = lookup | models.Q(category__icontains=value)
        return queryset.filter(lookup)

    def search_name_authors_category(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with all plugins for which name or author
        or category matches the search value.
        """
        lookup = models.Q(name__icontains=value)
        lookup = lookup | models.Q(authors__icontains=value)
        lookup = lookup | models.Q(category__icontains=value)
        return queryset.filter(lookup)

    class Meta:
        model = PluginMeta
        fields = ['id', 'name', 'name_exact', 'title', 'type', 'category', 'authors',
                  'owner_username', 'min_creation_date', 'max_creation_date',
                  'name_title_category', 'name_authors_category']


class PluginMetaStar(models.Model):
    """
    Model class that defines a plugin's star (when a user makes the plugin a favorite
    plugin).
    """
    meta = models.ForeignKey(PluginMeta, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('meta', 'user',)

    def __str__(self):
        return str(self.id)


class PluginMetaStarFilter(FilterSet):
    plugin_name = django_filters.CharFilter(field_name='meta__name', lookup_expr='exact')

    class Meta:
        model = PluginMetaStar
        fields = ['id', 'plugin_name']


def uploaded_file_path(instance, filename):
    # file will be stored to Swift at:
    # SWIFT_CONTAINER_NAME/<original_owner_username>/uploads/<today_path>/<filename>
    owner = instance.meta.owner.all()[0]
    username = owner.username
    today = timezone.now()
    today_path = today.strftime("%Y/%m/%d/%H/%M")
    return '{0}/{1}/{2}/{3}'.format(username, 'uploads', today_path, filename)


class Plugin(models.Model):
    """
    Model class that defines the versioned plugin.
    """
    # default resource limits inserted at registration time
    defaults = {
        'min_cpu_limit': 1000,  # in millicores
        'min_memory_limit': 200,  # in Mi
        'max_limit': 2147483647  # maxint
    }
    creation_date = models.DateTimeField(auto_now_add=True)
    version = models.CharField(max_length=10)
    dock_image = models.CharField(max_length=500)
    descriptor_file = models.FileField(max_length=512, upload_to=uploaded_file_path)
    execshell = models.CharField(max_length=50, blank=True)
    selfpath = models.CharField(max_length=512, blank=True)
    selfexec = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=800, blank=True)
    min_gpu_limit = models.IntegerField(null=True, blank=True, default=0)
    max_gpu_limit = models.IntegerField(null=True, blank=True, default=0)
    min_number_of_workers = models.IntegerField(null=True, blank=True, default=1)
    max_number_of_workers = models.IntegerField(null=True, blank=True,
                                                default=defaults['max_limit'])
    min_cpu_limit = CPUField(null=True, blank=True,
                             default=defaults['min_cpu_limit'])  # In millicores
    max_cpu_limit = CPUField(null=True, blank=True,
                             default=defaults['max_limit'])  # In millicores
    min_memory_limit = MemoryField(null=True, blank=True,
                                   default=defaults['min_memory_limit'])  # In Mi
    max_memory_limit = MemoryField(null=True, blank=True, default=defaults['max_limit'])
    meta = models.ForeignKey(PluginMeta, on_delete=models.CASCADE, related_name='plugins')

    class Meta:
        unique_together = ('meta', 'version',)
        ordering = ('meta', '-creation_date',)

    def __str__(self):
        return self.meta.name

    def get_plugin_parameter_names(self):
        """
        Custom method to get the list of plugin parameter names.
        """
        params = self.parameters.all()
        return [param.name for param in params]


class PluginFilter(FilterSet):
    """
    Filter class for the Plugin model.
    """
    min_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='gte')
    max_creation_date = django_filters.DateFilter(field_name='creation_date',
                                                  lookup_expr='lte')
    owner_username = django_filters.CharFilter(
        field_name='meta__owner__username', lookup_expr='exact')
    name = django_filters.CharFilter(field_name='meta__name', lookup_expr='icontains')
    name_exact = django_filters.CharFilter(field_name='meta__name', lookup_expr='exact')
    title = django_filters.CharFilter(field_name='meta__title', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='meta__category',
                                         lookup_expr='icontains')
    type = django_filters.CharFilter(field_name='meta__type', lookup_expr='exact')
    description = django_filters.CharFilter(field_name='description',
                                            lookup_expr='icontains')
    name_title_category = django_filters.CharFilter(method='search_name_title_category')
    name_latest = django_filters.CharFilter(method='search_latest')
    name_exact_latest = django_filters.CharFilter(method='search_latest')

    def search_name_title_category(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with all plugins for which name or title
        or category matches the search value.
        """
        # construct the full lookup expression.
        lookup = models.Q(meta__name__icontains=value)
        lookup = lookup | models.Q(meta__title__icontains=value)
        lookup = lookup | models.Q(meta__category__icontains=value)
        return queryset.filter(lookup)

    def search_latest(self, queryset, name, value):
        """
        Custom method to get a filtered queryset with the latest version according to
        creation date of all plugins whose name matches the search value.
        """
        if name == 'name_exact_latest':
            qs = queryset.filter(meta__name=value)
            return qs.order_by('-creation_date')[:1]
        else:
            qs = queryset.filter(meta__name__icontains=value)
            qs = qs.order_by('meta', '-creation_date')
            result_id_list = []
            meta_id = 0
            for pl in qs:
                pl_meta_id = pl.meta.id
                if pl_meta_id != meta_id:
                    result_id_list.append(pl.id)
                    meta_id = pl_meta_id
            return qs.filter(pk__in=result_id_list)

    class Meta:
        model = Plugin
        fields = ['id', 'name', 'name_latest', 'name_exact', 'name_exact_latest',
                  'dock_image', 'type', 'category', 'owner_username', 'min_creation_date',
                  'max_creation_date', 'title', 'version', 'description',
                  'name_title_category']


class PluginParameter(models.Model):
    """
    Model class that defines a plugin parameter.
    """
    name = models.CharField(max_length=50)
    flag = models.CharField(max_length=52)
    short_flag = models.CharField(max_length=52, blank=True)
    action = models.CharField(max_length=20, default='store')
    optional = models.BooleanField(default=False)
    type = models.CharField(choices=TYPE_CHOICES, default='string', max_length=10)
    help = models.TextField(blank=True)
    ui_exposed = models.BooleanField(default=True)
    plugin = models.ForeignKey(Plugin, on_delete=models.CASCADE,
                               related_name='parameters')

    class Meta:
        ordering = ('plugin',)

    def __str__(self):
        return self.name

    def get_default(self):
        """
        Custom method to get the default parameter instance regardless of its type.
        """
        default_attr_name = '%s_default' % self.type
        return getattr(self, default_attr_name, None)


class DefaultStrParameter(models.Model):
    """
    Model class that defines a default value for a plugin parameter of type string.
    """
    value = models.CharField(max_length=600, blank=True)
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='string_default')

    def __str__(self):
        return self.value


class DefaultIntParameter(models.Model):
    """
    Model class that defines a default value for a plugin parameter of type integer.
    """
    value = models.IntegerField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='integer_default')

    def __str__(self):
        return str(self.value)


class DefaultFloatParameter(models.Model):
    """
    Model class that defines a default value for a plugin parameter of type float.
    """
    value = models.FloatField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='float_default')

    def __str__(self):
        return str(self.value)


class DefaultBoolParameter(models.Model):
    """
    Model class that defines a default value for a plugin parameter of type boolean.
    """
    value = models.BooleanField()
    plugin_param = models.OneToOneField(PluginParameter, on_delete=models.CASCADE,
                                        related_name='boolean_default')

    def __str__(self):
        return str(self.value)
