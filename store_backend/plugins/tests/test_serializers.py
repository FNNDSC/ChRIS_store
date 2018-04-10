
import io
import json

from django.test import TestCase, tag
from django.contrib.auth.models import User

from rest_framework import serializers

from plugins.models import Plugin, PluginParameter
from plugins.serializers import PluginSerializer, PluginParameterSerializer

class PluginSerializerTests(TestCase):
    
    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__,
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        self.plg_repr = {}
        self.plg_repr['type'] = 'fs'
        self.plg_repr['authors'] = 'DEV FNNDSC'
        self.plg_repr['title'] = 'Dir plugin'
        self.plg_repr['description'] = 'Dir test plugin'
        self.plg_repr['license'] = 'MIT'
        self.plg_repr['version'] = 'v0.1'
        self.plg_repr['execshell'] = 'python3'
        self.plg_repr['selfpath'] = '/usr/src/simplefsapp'
        self.plg_repr['selfexec'] = 'simplefsapp.py'
        self.plg_repr['parameters'] = self.plugin_parameters

        user = User.objects.create_user(username=self.username, email=self.email,
                                 password=self.password)

        # create a plugin
        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name, owner=user)
        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            optional=self.plugin_parameters[0]['optional'])
        param_names = plugin.get_plugin_parameter_names()
        self.assertEquals(param_names, [self.plugin_parameters[0]['name']])

    def test_read_app_representation(self):
        """
        Test whether custom read_app_representation method returns an appropriate plugin
        representation dictionary from an uploaded json representation file.
        """
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            self.assertEquals(PluginSerializer.read_app_representation(f), self.plg_repr)

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
        when the descriptor cannot be converted to a a non-negative integer.
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

    def test_validate_app_parameters(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plugin_parameters
        parameter_list[0]['type'] = 'booleano'
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)
        parameter_list[0]['type'] = 'path'
        parameter_list[0]['optional'] = None
        with self.assertRaises(serializers.ValidationError):
            plg_serializer.validate_app_parameters(parameter_list)
        parameter_list[0]['optional'] = True

    def test_validate_check_required_execshell(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        del self.plg_repr['execshell'] # remove required 'execshell' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_selfpath(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        del self.plg_repr['selfpath'] # remove required 'selfpath' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_selfexec(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        del self.plg_repr['selfexec'] # remove required 'selfexec' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_check_required_parameters(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        del self.plg_repr['parameters'] # remove required 'parameters' from representation
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_remove_empty_min_number_of_workers(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_number_of_workers'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_number_of_workers', plg_serializer.validate(data))

    def test_validate_remove_empty_max_number_of_workers(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_number_of_workers'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_number_of_workers', plg_serializer.validate(data))

    def test_validate_remove_empty_min_gpu_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_gpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_gpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_gpu_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_gpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_gpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_min_cpu_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_cpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_cpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_cpu_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_cpu_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_cpu_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_min_memory_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_memory_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('min_memory_limit', plg_serializer.validate(data))

    def test_validate_remove_empty_max_memory_limit(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['max_memory_limit'] = ''
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            self.assertNotIn('max_memory_limit', plg_serializer.validate(data))

    def test_validate_workers_limits(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_number_of_workers'] = 2
        self.plg_repr['max_number_of_workers'] = 1
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_cpu_limits(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_cpu_limit'] = 200
        self.plg_repr['max_cpu_limit'] = 100
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_memory_limits(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_memory_limit'] = 100000
        self.plg_repr['max_memory_limit'] = 10000
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_gpu_limits(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        self.plg_repr['min_gpu_limit'] = 2
        self.plg_repr['max_gpu_limit'] = 1
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)

    def test_validate_validate_app_parameters(self):
        """
        Test whether custom validate_app_parameters method raises a ValidationError when
        a plugin's parameter has an unsupported type or any of its descriptors failed
        default validation.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        plg_serializer = PluginSerializer(plugin)
        parameter_list = self.plg_repr['parameters']
        parameter_list[0]['type'] = 'booleano'
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)
        parameter_list[0]['type'] = 'path'
        parameter_list[0]['optional'] = None
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            data = {'descriptor_file': f}
            with self.assertRaises(serializers.ValidationError):
                plg_serializer.validate(data)