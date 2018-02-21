
from rest_framework import serializers

from .models import Plugin, PluginParameter
from .models import TYPES

class PluginSerializer(serializers.HyperlinkedModelSerializer):
    parameters = serializers.HyperlinkedIdentityField(view_name='pluginparameter-list')
    owner = serializers.HyperlinkedRelatedField(view_name='user-detail', read_only=True)
    descriptor_file = serializers.FileField(write_only=True)
    
    class Meta:
        model = Plugin
        fields = ('url', 'name', 'creation_date', 'modification_date', 'dock_image',
                  'public_repo', 'type', 'authors', 'title', 'category', 'description',
                  'documentation', 'license', 'version', 'parameters', 'owner',
                  'descriptor_file', 'execshell', 'selfpath', 'selfexec')

    def is_valid(self, raise_exception=False):
        """
        Overriden to generate a properly formatted message for validation errors
        """
        valid = super(PluginSerializer, self).is_valid()
        if raise_exception and not valid:
            raise serializers.ValidationError({'detail': str(self._errors)})
        return valid

    def save_descriptors(self):
        """
        Custom method to check whether a new feef owner is a system-registered user.
        """
        plugin_name = self.validated_data.get("name")
        plugin = Plugin.objects.get(name=plugin_name)
        app_repr = plugin.read_descriptor_file()
        try:
            # save plugin's attributes to the db
            self.save(type = app_repr['type'],
                      authors = app_repr['authors'],
                      title = app_repr['title'],
                      category = app_repr['category'],
                      description = app_repr['description'],
                      documentation = app_repr['documentation'],
                      license = app_repr['license'],
                      version = app_repr['version'],
                      execshell = app_repr['execshell'],
                      selfpath = app_repr['selfpath'],
                      selfexec = app_repr['selfexec'])
            import pdb;pdb.set_trace()
            # save plugin's parameters to the db
            params = app_repr['parameters']
            for param in params:
                self._save_plugin_param(plugin, param)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(
                {'detail': e})

    def _save_plugin_param(self, plugin, param):
        """
        Internal method to save a plugin parameter into the DB.
        """
        # save plugin parameter to the db
        plugin_param = PluginParameter()
        serializer = PluginParameterSerializer(plugin_param)
        param_type = [key for key in TYPES if TYPES[key] == param['type']][0]
        param_default = ""
        if param['default']:
            param_default = str(param['default'])
        serializer.save(plugin = plugin,
                        name = param['name'],
                        type = param_type,
                        optional = param['optional'],
                        default = param_default,
                        help = param['help'])


class PluginParameterSerializer(serializers.HyperlinkedModelSerializer):
    plugin = serializers.HyperlinkedRelatedField(view_name='plugin-detail',
                                                 read_only=True)    
    class Meta:
        model = PluginParameter
        fields = ('url', 'name', 'type', 'optional', 'default', 'help', 'plugin')

    def is_valid(self, raise_exception=False):
        """
        Overriden to generate a properly formatted message for validation errors
        """
        valid = super(PluginParameterSerializer, self).is_valid()
        if raise_exception and not valid:
            raise serializers.ValidationError({'detail': str(self._errors)})
        return valid