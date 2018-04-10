
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
        plugin = super(PluginSerializer, self).save(**kwargs)
        # delete plugin's parameters from the db
        if plugin.parameters:
            plugin.parameters.all().delete()
        for param_serializer in self.parameter_serializers:
            param_serializer.save(plugin=plugin)
        return plugin

    def validate(self, data):
        """
        Overriden to validate descriptors in the plugin app representation.
        """
        app_repr = self.read_app_representation(data['descriptor_file'])

        # check for required descriptors in the app representation
        self.check_required_descriptor(app_repr, 'execshell')
        self.check_required_descriptor(app_repr, 'selfpath')
        self.check_required_descriptor(app_repr, 'selfexec')
        self.check_required_descriptor(app_repr, 'parameters')

        # delete from the request those integer descriptors with an empty string or
        # otherwise validate them
        if ('min_number_of_workers' in app_repr) and (app_repr['min_number_of_workers'] == ''):
            del app_repr['min_number_of_workers']
        elif 'min_number_of_workers' in app_repr:
            app_repr['min_number_of_workers'] = self.validate_app_workers_descriptor(
                app_repr['min_number_of_workers'])

        if ('max_number_of_workers' in app_repr) and (app_repr['max_number_of_workers'] == ''):
            del app_repr['max_number_of_workers']
        elif 'max_number_of_workers' in app_repr:
            app_repr['max_number_of_workers'] = self.validate_app_workers_descriptor(
                app_repr['max_number_of_workers'])

        if ('min_gpu_limit' in app_repr) and (app_repr['min_gpu_limit'] == ''):
            del app_repr['min_gpu_limit']
        elif 'min_gpu_limit' in app_repr:
            app_repr['min_gpu_limit'] = self.validate_app_gpu_descriptor(
                app_repr['min_gpu_limit'])

        if ('max_gpu_limit' in app_repr) and (app_repr['max_gpu_limit'] == ''):
            del app_repr['max_gpu_limit']
        elif 'max_gpu_limit' in app_repr:
            app_repr['max_gpu_limit'] = self.validate_app_gpu_descriptor(
                app_repr['max_gpu_limit'])

        # validations for descriptors with custom fields happen in the field itself
        if ('min_cpu_limit' in app_repr) and (app_repr['min_cpu_limit'] == ''):
            del app_repr['min_cpu_limit']
        if ('max_cpu_limit' in app_repr) and (app_repr['max_cpu_limit'] == ''):
            del app_repr['max_cpu_limit']
        if ('min_memory_limit' in app_repr) and app_repr['min_memory_limit'] == '':
            del app_repr['min_memory_limit']
        if ('max_memory_limit' in app_repr) and app_repr['max_memory_limit'] == '':
            del app_repr['max_memory_limit']

        # validate limits
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
        self.validate_app_parameters(app_repr['parameters'])

        # update the request data and run all validators for the plugin fields
        del app_repr['parameters']
        data.update(app_repr)
        self.run_validators(data)
        return data

    def validate_app_parameters(self, parameter_list):
        """
        Custom method to validate plugin parameters.
        """
        self.parameter_serializers = []
        for param in parameter_list:
            # translate from back-end type to front-end type, eg. bool->boolean
            param_type = [key for key in TYPES if TYPES[key] == param['type']]
            if not param_type:
                raise serializers.ValidationError("Invalid parameter type %s" %
                                                  param['type'])
            param['type'] = param_type[0]
            if param['default']:
                param['default'] = str(param['default'])
            else:
                param['default'] = ''
            param_serializer = PluginParameterSerializer(data=param)
            param_serializer.is_valid(raise_exception=True)
            self.parameter_serializers.append(param_serializer)

    @staticmethod
    def validate_app_workers_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum workers descriptors.
        """
        error_msg = "Minimum and maximum number of workers must be positive integers"
        int_d = PluginSerializer.validate_app_int_descriptor(descriptor, error_msg)
        if int_d < 1:
            raise serializers.ValidationError(error_msg)
        return int_d

    @staticmethod
    def validate_app_gpu_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum gpu descriptors.
        """
        error_msg = "Minimum and maximum gpu must be non-negative integers"
        return PluginSerializer.validate_app_int_descriptor(descriptor, error_msg)

    @staticmethod
    def validate_app_int_descriptor(descriptor, error_msg=''):
        """
        Custom method to validate a positive integer descriptor.
        """
        try:
            int_d = int(descriptor)
            assert int_d >= 0
        except (ValueError, AssertionError):
            raise serializers.ValidationError(error_msg)
        return int_d

    @staticmethod
    def validate_app_descriptor_limits(app_repr, min_descriptor_name, max_descriptor_name,
                                       error_msg=''):
        """
        Custom method to validate that a descriptor's minimum is smaller than its maximum.
        """
        if (min_descriptor_name in app_repr) and (max_descriptor_name in app_repr) \
                and (app_repr[max_descriptor_name] < app_repr[min_descriptor_name]):
            raise serializers.ValidationError(error_msg)

    @staticmethod
    def check_required_descriptor(app_repr, descriptor_name):
        """
        Custom method to check that a required descriptor is in the plugin app
        representation.
        """
        if not (descriptor_name in app_repr):
            raise serializers.ValidationError("%s must be a key of the app representation"
                                              " dictionary" % descriptor_name)

    @staticmethod
    def read_app_representation(app_representation_file):
        """
        Custom method to read the submitted plugin app representation file.
        """
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