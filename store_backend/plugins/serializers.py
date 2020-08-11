
import json
import re

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import serializers

from .models import PluginMeta, PluginMetaStar, Plugin, PluginParameter, TYPES
from .models import DefaultFloatParameter, DefaultIntParameter, DefaultBoolParameter
from .models import DefaultStrParameter
from .fields import CPUInt, MemoryInt


class PluginMetaSerializer(serializers.HyperlinkedModelSerializer):
    stars = serializers.ReadOnlyField(source='fan.count')
    owner = serializers.HyperlinkedRelatedField(many=True, view_name='user-detail',
                                                read_only=True)
    new_owner = serializers.CharField(min_length=4, max_length=32, write_only=True,
                                      required=False)
    plugins = serializers.HyperlinkedIdentityField(view_name='pluginmeta-plugin-list')

    class Meta:
        model = PluginMeta
        fields = ('url', 'id', 'creation_date', 'modification_date', 'name', 'title',
                  'stars', 'public_repo', 'license', 'type', 'icon', 'category',
                  'authors', 'documentation', 'plugins', 'owner', 'new_owner')

    def validate_new_owner(self, new_owner):
        """
        Overriden to check whether a new plugin owner is a system-registered user.
        """
        try:
            # check if new owner is a system-registered user
            owner = User.objects.get(username=new_owner)
        except ObjectDoesNotExist:
            msg = "User %s is not a registered user." % new_owner
            raise serializers.ValidationError(msg)
        return owner

    def update(self, instance, validated_data):
        """
        Overriden to add modification date.
        """
        instance.modification_date = timezone.now()
        instance.save()
        return super(PluginMetaSerializer, self).update(instance, validated_data)


class PluginMetaStarSerializer(serializers.HyperlinkedModelSerializer):
    plugin_name = serializers.CharField(max_length=100, source='meta.name')
    meta_id = serializers.ReadOnlyField(source='meta.id')
    user_id = serializers.ReadOnlyField(source='user.id')
    username = serializers.ReadOnlyField(source='user.username')
    meta = serializers.HyperlinkedRelatedField(view_name='pluginmeta-detail',
                                               read_only=True)
    user = serializers.HyperlinkedRelatedField(view_name='user-detail', read_only=True)

    class Meta:
        model = PluginMetaStar
        fields = ('url', 'id', 'plugin_name', 'meta_id', 'user_id', 'username', 'meta',
                  'user')

    def create(self, validated_data):
        """
        Overriden to check if plugin meta and user are unique together before saving.
        """
        self.validate_meta_user(validated_data['user'], validated_data['meta'])
        return super(PluginMetaStarSerializer, self).create(validated_data)

    def validate_plugin_name(self, plugin_name):
        """
        Overriden to check whether a plugin with the provided name exists in the DB.
        """
        try:
            # check whether plugin_name is a system-registered plugin
            pl_meta = PluginMeta.objects.get(name=plugin_name)
        except ObjectDoesNotExist:
            msg = "Could not find a plugin with name %s." % plugin_name
            raise serializers.ValidationError(msg)
        return pl_meta

    @staticmethod
    def validate_meta_user(user, meta):
        """
        Custom method to check if plugin meta and user are unique together.
        """
        try:
            PluginMetaStar.objects.get(meta=meta, user=user)
        except ObjectDoesNotExist:
            pass
        else:
            msg = "Plugin named %s is already a favorite of user %s." % (meta.name, user)
            raise serializers.ValidationError({'non_field_errors': [msg]})


class PluginSerializer(serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(max_length=100, source='meta.name')
    title = serializers.ReadOnlyField(source='meta.title')
    public_repo = serializers.URLField(max_length=300, source='meta.public_repo')
    license = serializers.ReadOnlyField(source='meta.license')
    type = serializers.ReadOnlyField(source='meta.type')
    icon = serializers.ReadOnlyField(source='meta.icon')
    category = serializers.ReadOnlyField(source='meta.category')
    authors = serializers.ReadOnlyField(source='meta.authors')
    documentation = serializers.ReadOnlyField(source='meta.documentation')
    stars = serializers.ReadOnlyField(source='meta.fan.count')
    parameters = serializers.HyperlinkedIdentityField(view_name='pluginparameter-list')
    meta = serializers.HyperlinkedRelatedField(view_name='pluginmeta-detail',
                                               read_only=True)
    descriptor_file = serializers.FileField(write_only=True)

    class Meta:
        model = Plugin
        fields = ('url', 'id', 'creation_date', 'name', 'version', 'dock_image',
                  'public_repo', 'icon', 'type', 'stars', 'authors', 'title', 'category',
                  'description', 'documentation', 'license', 'execshell', 'selfpath',
                  'selfexec', 'min_number_of_workers', 'max_number_of_workers',
                  'min_cpu_limit', 'max_cpu_limit', 'min_memory_limit',
                  'max_memory_limit', 'min_gpu_limit', 'max_gpu_limit', 'parameters',
                  'meta', 'descriptor_file')

    def create(self, validated_data):
        """
        Overriden to validate and save all the plugin descriptors and parameters
        associated with the plugin when creating it.
        """
        # gather the data that belongs to the plugin meta
        meta_dict = validated_data.pop('meta')
        meta_data = {'name': meta_dict['name'],
                     'public_repo': meta_dict['public_repo'],
                     'title': validated_data.pop('title', ''),
                     'license': validated_data.pop('license', ''),
                     'type': validated_data.pop('type', ''),
                     'icon': validated_data.pop('icon', ''),
                     'category': validated_data.pop('category', ''),
                     'authors': validated_data.pop('authors', ''),
                     'documentation': validated_data.pop('documentation', '')}

        # check whether plugin_name does not exist and validate the plugin meta data
        try:
            meta = PluginMeta.objects.get(name=meta_data['name'])
            meta_serializer = PluginMetaSerializer(meta, data=meta_data)
        except ObjectDoesNotExist:
            meta_serializer = PluginMetaSerializer(data=meta_data)
        meta_serializer.is_valid(raise_exception=True)

        #  create the full list of owners for the plugin name or raise error
        owner = validated_data.pop('owner')
        owner = self.validate_name_owner(owner[0], meta_data['name'])
        #  validate name,version are unique
        self.validate_name_version(validated_data['version'], meta_data['name'])

        # run all default validators for the full set of plugin fields
        request_parameters = validated_data['parameters']
        del validated_data['parameters']
        validated_data['public_repo'] = meta_dict['public_repo']
        validated_data['name'] = meta_dict['name']
        new_plg_serializer = PluginSerializer(data=validated_data)
        new_plg_serializer.validate = lambda x: x  # no need to rerun custom validaton
        new_plg_serializer.is_valid(raise_exception=True)

        # validate all the plugin parameters and their default values
        parameters_serializers = []
        for request_param in request_parameters:
            default = request_param.pop('default', None)
            param_serializer = PluginParameterSerializer(data=request_param)
            param_serializer.is_valid(raise_exception=True)
            serializer_dict = {'serializer': param_serializer,
                               'default_serializer': None}
            if default is not None:
                param_type = request_param['type']
                default_param_serializer = DEFAULT_PARAMETER_SERIALIZERS[param_type](
                    data={'value': default})
                default_param_serializer.is_valid(raise_exception=True)
                serializer_dict['default_serializer'] = default_param_serializer
            parameters_serializers.append(serializer_dict)

        # if no validation errors at this point then save everything to the DB!

        pl_meta = meta_serializer.save(owner=owner)
        validated_data = new_plg_serializer.validated_data
        validated_data['meta'] = pl_meta
        # the next is necessary because the descriptor_file's FileField needs an instance
        # of a plugin before saving to the the DB since its "uploaded_file_path" function
        # needs to access instance.owner (now an m2m relationship)
        descriptor_file = validated_data.pop('descriptor_file')
        plugin = super(PluginSerializer, self).create(validated_data)
        plugin.descriptor_file = descriptor_file
        plugin.save()
        for param_serializer_dict in parameters_serializers:
            param = param_serializer_dict['serializer'].save(plugin=plugin)
            if param_serializer_dict['default_serializer'] is not None:
                param_serializer_dict['default_serializer'].save(plugin_param=param)

        return plugin

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

            self.validate_app_version(app_repr['version'])

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
    def validate_app_version(version):
        """
        Custom method to check that a proper version number format has been submitted.
        """
        if not re.match(r"^[0-9.]+$", version):
            raise serializers.ValidationError(
                {'descriptor_file':
                     ["Invalid plugin app version number format %s." % version]})
        return version

    @staticmethod
    def validate_name_version(version, name):
        """
        Custom method to check if plugin name and version are unique together.
        """
        try:
            Plugin.objects.get(meta__name=name, version=version)
        except ObjectDoesNotExist:
            pass
        else:
            msg = "Plugin with name '%s and version %s already exists." % (name, version)
            raise serializers.ValidationError({'non_field_errors': [msg]})

    @staticmethod
    def validate_name_owner(owner, name):
        """
        Custom method to check if plugin name already exists and this user is not an
        owner. A user that is not an owner of a plugin is not allowed to post new
        versions of it.
        """
        owners = [owner]
        try:
            # check whether plugin_name is a system-registered plugin name
            pl_meta = PluginMeta.objects.get(name=name)
        except ObjectDoesNotExist:
            pl_meta = None
        if pl_meta is not None:
            owners = list(pl_meta.owner.all())
            if owner not in owners:
                raise serializers.ValidationError(
                    {'name': ["Plugin name %s is already owned by another user." % name]})
        return owners

    @staticmethod
    def validate_app_parameters(parameter_list):
        """
        Custom method to validate plugin parameters.
        """
        for param in parameter_list:
            if 'type' not in param:
                raise serializers.ValidationError(
                    {'descriptor_file': ["Parameter type is required."]})
            # translate from back-end type to front-end type, eg. bool->boolean
            param_type = [key for key in TYPES if TYPES[key] == param['type']]
            if not param_type:
                raise serializers.ValidationError(
                    {'descriptor_file': ["Invalid parameter type %s." % param['type']]})
            param['type'] = param_type[0]
            default = param['default'] if 'default' in param else None
            optional = param['optional'] if 'optional' in param else None
            if optional:
                if param['type'] in ('path', 'unextpath'):
                    raise serializers.ValidationError(
                        {'descriptor_file': ["Parameters of type 'path' or 'unextpath' "
                                             "cannot be optional."]})
                if default is None:
                    raise serializers.ValidationError(
                        {'descriptor_file': ["A default value is required for optional "
                                             "parameters."]})
            elif 'ui_exposed' in param and not param['ui_exposed']:
                raise serializers.ValidationError(
                    {'descriptor_file': ["Any parameter that is not optional must be "
                                         "exposed to the UI."]})
            if param['type'] == 'boolean' and 'action' not in param:
                param['action'] = 'store_false' if default else 'store_true'
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
        fields = ('url', 'id', 'name', 'type', 'optional', 'default', 'flag',
                  'short_flag', 'action', 'help', 'ui_exposed', 'plugin')

    def get_default(self, obj):
        """
        Overriden to get the default parameter value regardless of type.
        """
        default = obj.get_default()
        return default.value if default else None


class DefaultStrParameterSerializer(serializers.HyperlinkedModelSerializer):
    param_name = serializers.ReadOnlyField(source='plugin_param.name')
    type = serializers.SerializerMethodField()
    plugin_param = serializers.HyperlinkedRelatedField(view_name='pluginparameter-detail',
                                                       read_only=True)

    @staticmethod
    def get_type(obj):
        return obj.plugin_param.type

    class Meta:
        model = DefaultStrParameter
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


DEFAULT_PARAMETER_SERIALIZERS = {'string': DefaultStrParameterSerializer,
                                 'integer': DefaultIntParameterSerializer,
                                 'float': DefaultFloatParameterSerializer,
                                 'boolean': DefaultBoolParameterSerializer}
