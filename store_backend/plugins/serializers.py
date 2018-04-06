
import json

from rest_framework import serializers
from collectionjson.services import collection_serializer_is_valid

from .models import Plugin, PluginParameter, TYPES


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
        Overriden to generate a properly formatted message for validation errors.
        """
        return super(PluginSerializer, self).is_valid(raise_exception=raise_exception)

    def save(self, **kwargs):
        """
        Overriden to save the plugin's parameters into the DB.
        """
        import pdb;
        pdb.set_trace()
        plugin = super(PluginSerializer, self).save(**kwargs)
        for param_serializer in self.parameter_serializers:
            param_serializer.save(plugin=plugin)
        return plugin

    def validate(self, data):
        """
        Custom validation to check that minimum values are smaller than maximum values.
        """
        app_repr = self.read_app_representation(data['descriptor_file'])

        # delete from the request those integer descriptors with an empty string or
        # otherwise validate them

        if app_repr['min_number_of_workers'] == '':
            del app_repr['min_number_of_workers']
        else:
            err_msg = "Minimum number of workers must be positive integer"
            app_repr['min_number_of_workers'] = self.validate_app_workers_descriptor(
                app_repr['min_number_of_workers'], err_msg)

        if app_repr['max_number_of_workers'] == '':
            del app_repr['max_number_of_workers']
        else:
            err_msg = "Maximum number of workers must be positive integer"
            app_repr['max_number_of_workers'] = self.validate_app_workers_descriptor(
                app_repr['max_number_of_workers'], err_msg)

        if app_repr['min_gpu_limit'] == '':
            del app_repr['min_gpu_limit']
        else:
            err_msg = "Minimum gpu limit must be non-negative integer"
            app_repr['min_gpu_limit'] = self.validate_app_gpu_descriptor(
                app_repr['min_gpu_limit'], err_msg)

        if app_repr['max_gpu_limit'] == '':
            del app_repr['max_gpu_limit']
        else:
            err_msg = "Maximum gpu limit must be non-negative integer"
            app_repr['max_gpu_limit'] = self.validate_app_gpu_descriptor(
                app_repr['max_gpu_limit'], err_msg)

        # validations for these custom field descriptors happen in the field itself
        if app_repr['min_cpu_limit'] == '': del app_repr['min_cpu_limit']
        if app_repr['max_cpu_limit'] == '': del app_repr['max_cpu_limit']
        if app_repr['min_memory_limit'] == '': del app_repr['min_memory_limit']
        if app_repr['max_memory_limit'] == '': del app_repr['max_memory_limit']

        err_msg = "Minimum number of workers should be less than maximum number of workers"
        self.validate_app_descriptor_limits(app_repr, 'min_number_of_workers',
                                            'max_number_of_workers', err_msg)

        err_msg = "Minimum cpu limit should be less than maximum cpu limit"
        self.validate_app_descriptor_limits(app_repr, 'min_cpu_limit', 'max_cpu_limit',
                                            err_msg)

        err_msg = "Minimum memory limit should be less than maximum memory limit"
        self.validate_app_descriptor_limits(app_repr, 'min_memory_limit',
                                            'max_memory_limit', err_msg)

        err_msg = "Minimum gpu limit should be less than maximum gpu limit"
        self.validate_app_descriptor_limits(app_repr, 'min_gpu_limit', 'max_gpu_limit',
                                            err_msg)

        # validate plugin parameters in the request data
        if not 'parameters' in app_repr:
            serializers.ValidationError("'parameters' must be a key of the app "
                                        "representation dictionary")
        self.validate_app_parameters(app_repr['parameters'])

        # update the request data and run all validators for the plugin fields
        data.update(app_repr)
        self.run_validators(data)
        return data

    def validate_app_parameters(self, parameter_list):
        self.parameter_serializers = []
        for param in parameter_list:
            param['type'] = [key for key in TYPES if TYPES[key] == param['type']][0]
            if param['default']:
                param['default'] = str(param['default'])
            else:
                param['default'] = ''
            param_serializer = PluginParameterSerializer(data=param)
            param_serializer.is_valid(raise_exception=True)
            self.parameter_serializers.append(param_serializer)

    def validate_app_workers_descriptor(self, descriptor, error_msg=''):
        int_d = self.validate_app_int_descriptor(descriptor, error_msg)
        if int_d < 1:
            raise serializers.ValidationError(error_msg)
        return int_d

    def validate_app_gpu_descriptor(self, descriptor, error_msg=''):
        return self.validate_app_int_descriptor(descriptor, error_msg)

    @staticmethod
    def validate_app_int_descriptor(descriptor, error_msg=''):
        try:
            int_d = int(descriptor)
            assert int_d >= 0
        except (ValueError, AssertionError):
            raise serializers.ValidationError(error_msg)
        return int_d

    @staticmethod
    def validate_app_descriptor_limits(app_repr, min_descriptor_name, max_descriptor_name,
                                       error_msg=''):
        if (min_descriptor_name in app_repr) and (max_descriptor_name in app_repr) \
                and (app_repr[min_descriptor_name] < app_repr[max_descriptor_name]):
            raise serializers.ValidationError(error_msg)

    @staticmethod
    def read_app_representation(app_representation_file):
        app_repr = {}
        try:
            app_repr = json.loads(app_representation_file.read().decode())
            app_representation_file.seek(0)
        except Exception:
            serializers.ValidationError("Invalid json representation file")
        return app_repr


class PluginParameterSerializer(serializers.HyperlinkedModelSerializer):
    plugin = serializers.HyperlinkedRelatedField(view_name='plugin-detail',
                                                 read_only=True)

    class Meta:
        model = PluginParameter
        fields = ('url', 'name', 'type', 'optional', 'default', 'help', 'plugin')

    @collection_serializer_is_valid
    def is_valid(self, raise_exception=False):
        """
        Overriden to generate a properly formatted message for validation errors.
        """
        return super(PluginParameterSerializer, self).is_valid(
            raise_exception=raise_exception)