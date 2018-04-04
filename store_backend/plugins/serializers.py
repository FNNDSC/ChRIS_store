
from django.core.exceptions import ValidationError
from rest_framework import serializers
from collectionjson.services import collection_serializer_is_valid

from .models import Plugin, PluginParameter

class PluginSerializer(serializers.HyperlinkedModelSerializer):
    parameters = serializers.HyperlinkedIdentityField(view_name='pluginparameter-list')
    owner = serializers.HyperlinkedRelatedField(view_name='user-detail', read_only=True)
    descriptor_file = serializers.FileField(write_only=True)
    
    class Meta:
        model = Plugin
        fields = ('url', 'name', 'creation_date', 'modification_date', 'dock_image',
                  'public_repo', 'type', 'authors', 'title', 'category', 'description',
                  'documentation', 'license', 'version', 'parameters', 'owner',
                  'descriptor_file', 'execshell', 'selfpath', 'selfexec',
                  'min_number_of_workers', 'max_number_of_workers','min_cpu_limit',
                  'max_cpu_limit', 'min_memory_limit','max_memory_limit', 'min_gpu_limit',
                  'max_gpu_limit')

    @collection_serializer_is_valid
    def is_valid(self, raise_exception=False):
        """
        Overriden to generate a properly formatted message for validation errors
        """
        return super(PluginSerializer, self).is_valid(raise_exception=raise_exception)

    def save(self, **kwargs):
        """
        Overriden to validate and save the plugin's app representation descriptors into
        the DB
        """
        plugin = super(PluginSerializer, self).save(**kwargs)
        app_repr = plugin.read_descriptor_file()
        try:
            plugin.save_descriptors(app_repr)
        except (ValidationError, KeyError) as e:
            raise serializers.ValidationError({'detail': e})


class PluginParameterSerializer(serializers.HyperlinkedModelSerializer):
    plugin = serializers.HyperlinkedRelatedField(view_name='plugin-detail',
                                                 read_only=True)    
    class Meta:
        model = PluginParameter
        fields = ('url', 'name', 'type', 'optional', 'default', 'help', 'plugin')