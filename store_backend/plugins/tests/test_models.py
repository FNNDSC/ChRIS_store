
import json
import io
from unittest import mock

from django.test import TestCase, tag
from django.contrib.auth.models import User
from django.conf import settings

import swiftclient

from plugins.models import Plugin, PluginParameter

class PluginModelTests(TestCase):
    
    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__,
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        self.plg_repr = {}
        self.plg_repr['name'] = self.plugin_name
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
        Plugin.objects.get_or_create(name=self.plugin_name, owner=user)

    def test_get_plugin_parameter_names(self):
        """
        Test whether custom get_plugin_parameter_names method returns the names of all
        parameters of an existing plugin in a list.
        """
        plugin = Plugin.objects.get(name=self.plugin_name)
        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            optional=self.plugin_parameters[0]['optional'])
        param_names = plugin.get_plugin_parameter_names()
        self.assertEquals(param_names, [self.plugin_parameters[0]['name']])

    @tag('integration')
    def test_integration_read_descriptor_file(self):
        """
        Test whether custom method read_descriptor_file reads and returns the plugin
        representation from the JSON descriptor file.
        """
        # initiate a Swift service connection
        conn = swiftclient.Connection(
            user=settings.SWIFT_USERNAME,
            key=settings.SWIFT_KEY,
            authurl=settings.SWIFT_AUTH_URL,
        )
        # create container in case it doesn't already exist
        conn.put_container(settings.SWIFT_CONTAINER_NAME)

        # upload file to Swift storage
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            conn.put_object(settings.SWIFT_CONTAINER_NAME, 'test/uploads/file1.txt',
                            contents = f.read(), content_type = 'text/plain')

        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name)
        plugin.descriptor_file.name = 'test/uploads/file1.txt'
        json_repr = plugin.read_descriptor_file()
        self.assertEquals(json_repr, self.plg_repr)

    def test_save_descriptors(self):
        """
        Test whether custom save_descriptors method saves the plugin's app representation
        descriptors into the DB.
        """
        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name)
        plugin.save_descriptors(self.plg_repr)
        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name)
        self.assertEquals(plugin.type, 'fs')
        self.assertEquals(plugin.authors, 'DEV FNNDSC')
        self.assertEquals(plugin.title, 'Dir plugin')
        self.assertEquals(plugin.description,'Dir test plugin')
        self.assertEquals(plugin.license, 'MIT')
        self.assertEquals(plugin.version, 'v0.1')
        self.assertEquals(plugin.execshell, 'python3')
        self.assertEquals(plugin.selfpath, '/usr/src/simplefsapp')
        self.assertEquals(plugin.selfexec, 'simplefsapp.py')
        parameter = plugin.parameters.all()[0]
        self.assertEquals(parameter.name, self.plugin_parameters[0]['name'])