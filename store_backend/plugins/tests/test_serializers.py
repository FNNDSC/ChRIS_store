
import io
import json

from django.test import TestCase, tag
from django.contrib.auth.models import User

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
        representation dictionary from a json representation file.
        """
        with io.BytesIO(json.dumps(self.plg_repr).encode()) as f:
            self.assertEquals(PluginSerializer.read_app_representation(f), self.plg_repr)
