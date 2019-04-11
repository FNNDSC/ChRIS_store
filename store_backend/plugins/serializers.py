
import json

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import serializers

from .models import Plugin, PluginParameter, TYPES
from .models import DefaultFloatParameter, DefaultIntParameter, DefaultBoolParameter
from .models import DefaultPathParameter, DefaultStringParameter
from .fields import CPUInt, MemoryInt


class PluginSerializer(serializers.HyperlinkedModelSerializer):
    parameters = serializers.HyperlinkedIdentityField(view_name='pluginparameter-list')
    owner = serializers.HyperlinkedRelatedField(many=True, view_name='user-detail',
                                                read_only=True)
    descriptor_file = serializers.FileField(write_only=True)
    
    class Meta:
        model = Plugin
        fields = ('url', 'id', 'name', 'creation_date', 'modification_date', 'dock_image',
                  'public_repo', 'icon', 'type', 'authors', 'title', 'category',
                  'description', 'documentation', 'license', 'version', 'parameters',
                  'owner', 'descriptor_file', 'execshell', 'selfpath', 'selfexec',
                  'min_number_of_workers', 'max_number_of_workers','min_cpu_limit',
                  'max_cpu_limit', 'min_memory_limit','max_memory_limit', 'min_gpu_limit',
                  'max_gpu_limit')

    def create(self, validated_data):
        """
        Overriden to validate and save all the plugin descriptors and parameters
        associated with the plugin when creating it.
        """
        # assign the full list of owners for the plugin name or raise error
        owner = validated_data['owner'][0]
        validated_data['owner'] = self.validate_name_owner(owner, validated_data['name'])

        # run all default validators for the full set of plugin fields
        request_parameters = validated_data['parameters']
        del validated_data['parameters']
        new_plg_serializer = PluginSerializer(data=validated_data)
        new_plg_serializer.validate = lambda x: x  # no need to rerun custom validators
        new_plg_serializer.is_valid(raise_exception=True)

        # this is necessary because the descriptor_file's FileField needs an instance of
        # a plugin before saving to the the DB since its "uploaded_file_path" function
        # needs to access instance.owner (now an m2m relationship)
        descriptor_file = validated_data['descriptor_file']
        del validated_data['descriptor_file']

        plugin = super(PluginSerializer, self).create(validated_data)
        plugin.descriptor_file = descriptor_file
        plugin.save()

        # validate and save all the plugin parameters and their default values
        for request_param in request_parameters:
            default = request_param['default'] if 'default' in request_param else None
            del request_param['default']
            param_serializer = PluginParameterSerializer(data=request_param)
            param_serializer.is_valid(raise_exception=True)
            param = param_serializer.save(plugin=plugin)
            if default is not None:
                default_param_serializer = DEFAULT_PARAMETER_SERIALIZERS[param.type](
                    data={'value': default})
                default_param_serializer.is_valid(raise_exception=True)
                default_param_serializer.save(plugin_param=param)

        return plugin

    def update(self, instance, validated_data):
        """
        Overriden to add modification date.
        """
        validated_data.update({'modification_date': timezone.now()})
        return super(PluginSerializer, self).update(instance, validated_data)

    def validate(self, data):
        """
        Overriden to validate descriptors in the plugin app representation.
        """
        if not self.instance:
            app_repr = self.read_app_representation(data['descriptor_file'])

            # check for required descriptors in the app representation
            self.check_required_descriptor(app_repr, 'version')
            self.check_required_descriptor(app_repr, 'execshell')
            self.check_required_descriptor(app_repr, 'selfpath')
            self.check_required_descriptor(app_repr, 'selfexec')
            self.check_required_descriptor(app_repr, 'parameters')

            # delete from the request those integer descriptors with an empty string or
            # otherwise validate them
            if ('min_number_of_workers' in app_repr) and (
                    app_repr['min_number_of_workers'] == ''):
                del app_repr['min_number_of_workers']
            elif 'min_number_of_workers' in app_repr:
                app_repr['min_number_of_workers'] = self.validate_app_workers_descriptor(
                    app_repr['min_number_of_workers'])

            if ('max_number_of_workers' in app_repr) and (
                    app_repr['max_number_of_workers'] == ''):
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

            if ('min_cpu_limit' in app_repr) and (app_repr['min_cpu_limit'] == ''):
                del app_repr['min_cpu_limit']
            elif 'min_cpu_limit' in app_repr:
                app_repr['min_cpu_limit'] = self.validate_app_cpu_descriptor(
                    app_repr['min_cpu_limit'])

            if ('max_cpu_limit' in app_repr) and (app_repr['max_cpu_limit'] == ''):
                del app_repr['max_cpu_limit']
            elif 'max_cpu_limit' in app_repr:
                app_repr['max_cpu_limit'] = self.validate_app_cpu_descriptor(
                    app_repr['max_cpu_limit'])

            if ('min_memory_limit' in app_repr) and app_repr['min_memory_limit'] == '':
                del app_repr['min_memory_limit']
            elif 'min_memory_limit' in app_repr:
                app_repr['min_memory_limit'] = self.validate_app_memory_descriptor(
                    app_repr['min_memory_limit'])

            if ('max_memory_limit' in app_repr) and app_repr['max_memory_limit'] == '':
                del app_repr['max_memory_limit']
            elif 'max_memory_limit' in app_repr:
                app_repr['max_memory_limit'] = self.validate_app_memory_descriptor(
                    app_repr['max_memory_limit'])

            # validate limits
            err_msg = "The minimum number of workers should be less than the maximum."
            self.validate_app_descriptor_limits(app_repr, 'min_number_of_workers',
                                                'max_number_of_workers', err_msg)

            err_msg = "Minimum cpu limit should be less than maximum cpu limit."
            self.validate_app_descriptor_limits(app_repr, 'min_cpu_limit',
                                                'max_cpu_limit', err_msg)

            err_msg = "Minimum memory limit should be less than maximum memory limit."
            self.validate_app_descriptor_limits(app_repr, 'min_memory_limit',
                                                'max_memory_limit', err_msg)

            err_msg = "Minimum gpu limit should be less than maximum gpu limit."
            self.validate_app_descriptor_limits(app_repr, 'min_gpu_limit',
                                                'max_gpu_limit', err_msg)

            # validate plugin parameters in the request data
            app_repr['parameters'] = self.validate_app_parameters(app_repr['parameters'])

            # update the request data
            data.update(app_repr)
        return data

    @staticmethod
    def validate_name_owner(owner, name):
        """
        Custom method to check if plugin name already exists and this user is not an
        owner.
        """
        plg = Plugin.objects.filter(name=name).first()
        owners = [owner]
        if plg:
            owners = list(plg.owner.all())
            if owner not in owners:
                raise serializers.ValidationError(
                    {'name': ["Plugin name %s is already owned by another user." % name]})
        return owners

    @staticmethod
    def validate_new_owner(username):
        """
        Custom method to check whether a new plugin owner is a system-registered user.
        """
        try:
            # check if user is a system-registered user
            new_owner = User.objects.get(username=username)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                {'owner': ["User %s is not a registered user." % username]})
        return new_owner

    @staticmethod
    def validate_app_parameters(parameter_list):
        """
        Custom method to validate plugin parameters.
        """
        for param in parameter_list:
            # translate from back-end type to front-end type, eg. bool->boolean
            param_type = [key for key in TYPES if TYPES[key] == param['type']]
            if not param_type:
                raise serializers.ValidationError(
                    {'descriptor_file': ["Invalid parameter type %s." % param['type']]})
            param['type'] = param_type[0]
        return parameter_list

    @staticmethod
    def validate_app_workers_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum workers descriptors.
        """
        error_msg = "Minimum and maximum number of workers must be positive integers."
        int_d = PluginSerializer.validate_app_int_descriptor(descriptor, error_msg)
        if int_d < 1:
            raise serializers.ValidationError({'descriptor_file': [error_msg]})
        return int_d

    @staticmethod
    def validate_app_cpu_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum cpu descriptors.
        """
        try:
            return CPUInt(descriptor)
        except ValueError as e:
            raise serializers.ValidationError({'descriptor_file': [str(e)]})

    @staticmethod
    def validate_app_memory_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum memory descriptors.
        """
        try:
            return MemoryInt(descriptor)
        except ValueError as e:
            raise serializers.ValidationError({'descriptor_file': [str(e)]})

    @staticmethod
    def validate_app_gpu_descriptor(descriptor):
        """
        Custom method to validate plugin maximum and minimum gpu descriptors.
        """
        error_msg = "Minimum and maximum gpu must be non-negative integers."
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
            raise serializers.ValidationError({'descriptor_file': [error_msg]})
        return int_d

    @staticmethod
    def validate_app_descriptor_limits(app_repr, min_descriptor_name, max_descriptor_name,
                                       error_msg=''):
        """
        Custom method to validate that a descriptor's minimum is smaller than its maximum.
        """
        if (min_descriptor_name in app_repr) and (max_descriptor_name in app_repr) \
                and (app_repr[max_descriptor_name] < app_repr[min_descriptor_name]):
            raise serializers.ValidationError({'descriptor_file': [error_msg]})

    @staticmethod
    def check_required_descriptor(app_repr, descriptor_name):
        """
        Custom method to check that a required descriptor is in the plugin app
        representation.
        """
        if not (descriptor_name in app_repr):
            error_msg = "Descriptor %s must be in the app representation dictionary." \
                        % descriptor_name
            raise serializers.ValidationError({'descriptor_file': [error_msg]})

    @staticmethod
    def read_app_representation(app_representation_file):
        """
        Custom method to read the submitted plugin app representation file.
        """
        try:
            app_repr = json.loads(app_representation_file.read().decode())
            app_representation_file.seek(0)
        except Exception:
            error_msg = "Invalid json representation file."
            raise serializers.ValidationError({'descriptor_file': [error_msg]})
        return app_repr


class PluginParameterSerializer(serializers.HyperlinkedModelSerializer):
    plugin = serializers.HyperlinkedRelatedField(view_name='plugin-detail',
                                                 read_only=True)
    default = serializers.SerializerMethodField()

    class Meta:
        model = PluginParameter
        fields = ('url', 'id', 'name', 'type', 'optional', 'default', 'flag', 'action',
                  'help', 'plugin')

    def get_default(self, obj):
        """
        Overriden to get the default parameter value regardless of type.
        """
        default_parameter = getattr(obj, obj.type + '_default', None)
        return default_parameter.value if default_parameter else None


class DefaultStringParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultStringParameter
        fields = ('url', 'id', 'param_name', 'value', 'type', 'plugin_param')


class DefaultIntParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultIntParameter
        fields = ('url', 'id', 'param_name', 'value', 'type', 'plugin_param')


class DefaultFloatParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultFloatParameter
        fields = ('url', 'id', 'param_name', 'value', 'type', 'plugin_param')


class DefaultBoolParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultBoolParameter
        fields = ('url', 'id', 'param_name', 'value', 'type', 'plugin_param')


class DefaultPathParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultPathParameter
        fields = ('url', 'id', 'param_name', 'value', 'type', 'plugin_param')


DEFAULT_PARAMETER_SERIALIZERS = {'string': DefaultStringParameterSerializer,
                         'integer': DefaultIntParameterSerializer,
                         'float': DefaultFloatParameterSerializer,
                         'boolean': DefaultBoolParameterSerializer,
                         'path': DefaultPathParameterSerializer}
