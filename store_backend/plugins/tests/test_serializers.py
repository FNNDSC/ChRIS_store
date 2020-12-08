
import logging
import io
import json

from django.test import TestCase, tag
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from rest_framework import serializers

from plugins.models import PluginMeta, PluginMetaStar, Plugin, PluginParameter
from plugins.serializers import (PluginMetaSerializer, PluginMetaStarSerializer,
                                 PluginSerializer, PluginParameterSerializer)


class PluginMetaSerializerTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.plugin_name = 'simplefsapp'
        user = User.objects.create_user(username='foo', email='dev@babymri.org',
                                 password='foopassword')
        # create a plugin meta
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name)
        meta.owner.set([user])

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)

    def test_validate_new_owner(self):
        """
        Test whether overriden validate_new_owner method checks whether a new plugin
        owner is a system-registered user.
        """
        another_user = User.objects.create_user(username='another',
                                                email='anotherdev@babymri.org',
                                                password='anotherpassword')
        plg_meta_serializer = PluginMetaSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_meta_serializer.validate_new_owner("unknown")
        new_owner = plg_meta_serializer.validate_new_owner("another")
        self.assertEqual(new_owner, another_user)

    def test_update(self):
        """
        Test whether overriden update method changes modification date.
        """
        meta = PluginMeta.objects.get(name=self.plugin_name)
        initial_mod_date = meta.modification_date
        data = {'name': self.plugin_name, 'public_repo': 'http://github.com/plugin'}
        plg_meta_serializer = PluginMetaSerializer(meta, data)
        plg_meta_serializer.is_valid(raise_exception=True)
        meta = plg_meta_serializer.update(meta, plg_meta_serializer.validated_data)
        self.assertGreater(meta.modification_date, initial_mod_date)


class PluginMetaStarSerializerTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.plugin_name = 'simplefsapp'
        user = User.objects.create_user(username='foo', email='dev@babymri.org',
                                 password='foopassword')
        # create a plugin meta
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name)
        meta.owner.set([user])

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)

    def test_validate_plugin_name(self):
        """
        Test whether overriden validate_plugin_name method raises ValidationError
        if provided plugin name does not exist in the DB.
        """
        plg_meta = PluginMeta.objects.get(name=self.plugin_name)
        plg_meta_star_serializer = PluginMetaStarSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_meta_star_serializer.validate_plugin_name("unknown")
        meta = plg_meta_star_serializer.validate_plugin_name(self.plugin_name)
        self.assertEqual(meta, plg_meta)


class PluginSerializerTests(TestCase):
    
    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = 'simplefsapp'
        self.plugin_dock_image = 'fnndsc/pl-simplefsapp'
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                   'optional': True, 'flag': '--dir', 'short_flag': '-d',
                                   'default': '/', 'help': 'test plugin',
                                   'ui_exposed': True}]

        self.plg_data = {'description': 'Dir test plugin',
                         'version': '0.1',
                         'execshell': 'python3',
                         'selfpath': '/usr/src/simplefsapp',
                         'selfexec': 'simplefsapp.py'}

        self.plg_meta_data = {'title': 'Dir plugin',
                              'license': 'MIT',
                              'type': 'fs',
                              'icon': 'http://github.com/plugin',
                              'category': 'Dir',
                              'authors': 'DEV FNNDSC'}

        self.plg_repr = self.plg_data.copy()
        self.plg_repr.update(self.plg_meta_data)
        self.plg_repr['parameters'] = self.plugin_parameters

        user = User.objects.create_user(username=self.username, email=self.email,
                                 password=self.password)

        # create a plugin
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name)
        meta.owner.set([user])
        (plugin, tf) = Plugin.objects.get_or_create(meta=meta,
                                                    version=self.plg_repr['version'],
                                                    dock_image=self.plugin_dock_image)

        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            optional=self.plugin_parameters[0]['optional'],
            action=self.plugin_parameters[0]['action'],
            flag=self.plugin_parameters[0]['flag'],
            short_flag=self.plugin_parameters[0]['short_flag'],
        )
        param_names = plugin.get_plugin_parameter_names()
        self.assertEqual(param_names, [self.plugin_parameters[0]['name']])

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)

    def test_validate_app_version(self):
        """
        Test whether custom validate_app_version method raises a ValidationError when
        wrong version type or format has been submitted.
        """
        plg_serializer = PluginSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_version(1.2)
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_version('v1.2')

    def test_validate_name_version(self):
        """
        Test whether custom validate_name_version method raises a ValidationError when
        plugin name and version are not unique together.
        """
        plg_serializer = PluginSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_name_version(self.plg_repr['version'], self.plugin_name)

    def test_validate_name_image(self):
        """
        Test whether custom validate_name_image method raises a ValidationError when
        plugin name and docker image are not unique together.
        """
        plg_serializer = PluginSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_name_image(self.plugin_dock_image, self.plugin_name)

    def test_create_also_creates_meta_first_time_plugin_name_is_used(self):
        """
        Test whether overriden create also creates a new plugin meta when creating a
        plugin with a new name that doesn't already exist in the system.
        """
        user = User.objects.get(username=self.username)
        validated_data = self.plg_repr.copy()
        validated_data['parameters'][0]['type'] = 'string'
        validated_data['meta'] = {'name': 'testapp',
                                  'public_repo': 'https://github.com/FNNDSC'}
        validated_data['dock_image'] = 'fnndsc/pl-testapp'
        f = ContentFile(json.dumps(self.plg_repr).encode())
        f.name = 'testapp.json'
        validated_data['descriptor_file'] = f
        validated_data['owner'] = [user]
        plg_serializer = PluginSerializer()
        with self.assertRaises(PluginMeta.DoesNotExist):
            PluginMeta.objects.get(name='testapp')
        plg_serializer.create(validated_data)
        self.assertEqual(PluginMeta.objects.get(name='testapp').name, 'testapp')

    def test_create_does_not_create_meta_after_first_time_plugin_name_is_used(self):
        """
        Test whether overriden create does not create a new plugin meta when creating a
        plugin version with a name that already exists in the system.
        """
        user = User.objects.get(username=self.username)
        validated_data = self.plg_repr.copy()
        validated_data['parameters'][0]['type'] = 'string'
        validated_data['version'] = '0.2.2'
        validated_data['meta'] = {'name': self.plugin_name,
                                  'public_repo': 'https://github.com/FNNDSC'}
        validated_data['dock_image'] = 'fnndsc/pl-testapp'
        f = ContentFile(json.dumps(self.plg_repr).encode())
        f.name = 'testapp.json'
        validated_data['descriptor_file'] = f
        validated_data['owner'] = [user]
        plg_serializer = PluginSerializer()
        n_plg_meta = PluginMeta.objects.count()
        plg_meta = PluginMeta.objects.get(name=self.plugin_name)
        plugin = plg_serializer.create(validated_data)
        self.assertEqual(n_plg_meta, PluginMeta.objects.count())
        self.assertEqual(plugin.meta, plg_meta)

    def test_validate_name_owner(self):
        """
        Test whether custom validate_name_owner method raises a ValidationError when
        plugin name already exists and the user is not an owner.
        """
        user = User.objects.get(username=self.username)
        another_user = User.objects.create_user(username='another',
                                                email='anotherdev@babymri.org',
                                                password='anotherpassword')
        plg_serializer = PluginSerializer()
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_name_owner(another_user, self.plugin_name)
        owners = plg_serializer.validate_name_owner(another_user, 'new_name')
        self.assertIn(another_user, owners)
        owners = plg_serializer.validate_name_owner(user, self.plugin_name)
        self.assertIn(user, owners)

    def test_read_app_representation(self):
        """
        Test whether custom read_app_representation method returns an appropriate plugin
        representation dictionary from an uploaded json representation file.
        """
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            self.assertEqual(PluginSerializer.read_app_representation(f), self.plg_repr)

    def test_check_required_descriptor(self):
        """
        Test whether custom check_required_descriptor method raises a ValidationError
        when a required descriptor is missing from the plugin app representation.
        """
        del self.plg_repr['execshell']
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.check_required_descriptor(self.plg_repr, 'execshell')

    def test_validate_app_descriptor_limits(self):
        """
        Test whether custom validate_app_descriptor_limit method raises a ValidationError
        when the max limit is smaller than the min limit.
        """
        self.plg_repr['min_cpu_limit'] = 200
        self.plg_repr['max_cpu_limit'] = 100
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_descriptor_limits(self.plg_repr,
                                                            'min_cpu_limit',
                                                            'max_cpu_limit')

    def test_validate_app_int_descriptor(self):
        """
        Test whether custom validate_app_int_descriptor method raises a ValidationError
        when the descriptor cannot be converted to a non-negative integer.
        """
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_int_descriptor('one')
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_int_descriptor(-1)

    def test_validate_app_gpu_descriptor(self):
        """
        Test whether custom validate_app_gpu_descriptor method raises a ValidationError
        when the gpu descriptor cannot be converted to a non-negative integer.
        """
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_gpu_descriptor('one')
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_gpu_descriptor(-1)

    def test_validate_app_workers_descriptor(self):
        """
        Test whether custom validate_app_workers_descriptor method raises a ValidationError
        when the app worker descriptor cannot be converted to a positive integer.
        """
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_workers_descriptor('one')
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_workers_descriptor(0)

    def test_validate_app_cpu_descriptor(self):
        """
        Test whether custom validate_app_cpu_descriptor method raises a ValidationError
        when the app cpu descriptor cannot be converted to a fields.CPUInt.
        """
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_cpu_descriptor('100me')
            self.assertEqual(100, PluginSerializer.validate_app_cpu_descriptor('100m'))

    def test_validate_app_memory_descriptor(self):
        """
        Test whether custom validate_app_memory_descriptor method raises a ValidationError
        when the app memory descriptor cannot be converted to a fields.MemoryInt.
        """
        with self.assertRaises(serializers.ValidationError):
            PluginSerializer.validate_app_cpu_descriptor('100me')
            self.assertEqual(100, PluginSerializer.validate_app_cpu_descriptor('100mi'))
            self.assertEqual(100, PluginSerializer.validate_app_cpu_descriptor('100gi'))

    def test_validate_app_parameters_type(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin parameter has an unsupported type.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plugin_parameters
        parameter_list[0]['type'] = 'booleano'
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)

    def test_validate_app_parameters_default(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        an optional plugin parameter doesn't have a default value specified.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plugin_parameters
        parameter_list[0]['default'] = None
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)

    def test_validate_app_parameters_of_path_type_and_optional(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin parameter is optional anf of type 'path' or 'unextpath'.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plugin_parameters
        parameter_list[0]['type'] = 'path'
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)
        parameter_list[0]['type'] = 'unextpath'
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)

    def test_validate_app_parameters_not_ui_exposed_and_not_optional(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin parameter that is not optional is not exposed to the ui.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plugin_parameters
        parameter_list[0]['optional'] = False
        parameter_list[0]['ui_exposed'] = False
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)

    def test_validate_check_required_execshell(self):
        """
        Test whether the custom validate method raises a ValidationError when required
        'execshell' descriptor is missing from the plugin app representation.
        """
        del self.plg_repr['execshell'] # remove required 'execshell' from representation
        plg_serializer = PluginSerializer()
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_selfpath(self):
        """
        Test whether the custom validate method raises a ValidationError when required
        'selfpath' descriptor is missing from the plugin app representation.
        """
        plg_serializer = PluginSerializer()
        del self.plg_repr['selfpath'] # remove required 'selfpath' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_selfexec(self):
        """
        Test whether the custom validate method raises a ValidationError when required
        'selfexec' descriptor is missing from the plugin app representation.
        """
        plg_serializer = PluginSerializer()
        del self.plg_repr['selfexec'] # remove required 'selfexec' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_parameters(self):
        """
        Test whether the custom validate method raises a ValidationError when required
        'parameters' descriptor is missing from the plugin app representation.
        """
        plg_serializer = PluginSerializer()
        del self.plg_repr['parameters'] # remove required 'parameters' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_remove_empty_min_number_of_workers(self):
        """
        Test whether the custom validate method removes 'min_number_of_workers'
        descriptor from the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_number_of_workers'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_number_of_workers', plg_serializer.validate(data))

    def test_validate_remove_empty_max_number_of_workers(self):
        """
        Test whether the custom validate method removes 'max_number_of_workers'
        descriptor from the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_number_of_workers'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_number_of_workers', plg_serializer.validate(data))

    def test_validate_remove_empty_min_gpu_limit(self):
        """
        Test whether the custom validate method removes 'min_gpu_limit' descriptor from
        the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_gpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_gpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_gpu_limit(self):
        """
        Test whether the custom validate method removes 'max_gpu_limit' descriptor from
        the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_gpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_gpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_min_cpu_limit(self):
        """
        Test whether the custom validate method removes 'min_cpu_limit' descriptor from
        the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_cpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_cpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_cpu_limit(self):
        """
        Test whether the custom validate method removes 'max_cpu_limit' descriptor from
        the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_cpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_cpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_min_memory_limit(self):
        """
        Test whether the custom validate method removes 'min_memory_limit'
        descriptor from the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_memory_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_memory_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_memory_limit(self):
        """
        Test whether the custom validate method removes 'max_memory_limit'
        descriptor from the validated data when it is the empty string.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_memory_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_memory_limit', plg_serializer.validate(data))

    def test_validate_workers_limits(self):
        """
        Test whether custom validate method raises a ValidationError when the
        'max_number_of_workers' is smaller than the 'min_number_of_workers'.
        """
        plg_serializer = PluginSerializer()
        self.plg_repr['min_number_of_workers'] = 2
        self.plg_repr['max_number_of_workers'] = 1
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_cpu_limits(self):
        """
        Test whether custom validate method raises a ValidationError when the
        'max_cpu_limit' is smaller than the 'min_cpu_limit'.
        """
        plg_serializer = PluginSerializer()
        self.plg_repr['min_cpu_limit'] = 200
        self.plg_repr['max_cpu_limit'] = 100
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_memory_limits(self):
        """
        Test whether custom validate method raises a ValidationError when the
        'max_memory_limit' is smaller than the 'min_memory_limit'.
        """
        plg_serializer = PluginSerializer()
        self.plg_repr['min_memory_limit'] = 100000
        self.plg_repr['max_memory_limit'] = 10000
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_gpu_limits(self):
        """
        Test whether custom validate method raises a ValidationError when the
        'max_gpu_limit' is smaller than the 'max_gpu_limit'.
        """
        plg_serializer = PluginSerializer()
        self.plg_repr['min_gpu_limit'] = 2
        self.plg_repr['max_gpu_limit'] = 1
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_validate_app_parameters(self):
        """
        Test whether custom validate method validates submitted plugin's parameters.
        """
        plg_serializer = PluginSerializer()
        parameter_list = self.plg_repr['parameters']
        parameter_list[0]['type'] = 'booleano'
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_update_validated_data(self):
        """
        Test whether custom validate method updates validated data with the plugin app
        representation.
        """
        plg_serializer = PluginSerializer()
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            new_data = plg_serializer.validate(data)
            self.assertIn('version', new_data)
            self.assertIn('execshell', new_data)
            self.assertIn('selfpath', new_data)
            self.assertIn('selfexec', new_data)
            self.assertIn('parameters', new_data)
