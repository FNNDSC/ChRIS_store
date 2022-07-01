
import logging
import json
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, tag

from plugins.models import PluginMeta, PluginMetaCollaborator, Plugin, PluginParameter
from plugins.services import manager


class PluginManagerTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [
            {'name': 'dir', 'type': str.__name__, 'action': 'store',
             'optional': True, 'flag': '--dir', 'default': './',
             'help': 'test plugin'}]

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
        data = self.plg_meta_data.copy()
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name,
                                                      public_repo='http://gitgub.com',
                                                      **data)
        PluginMetaCollaborator.objects.create(meta=meta, user=user)
        data = self.plg_data.copy()
        (plugin, tf) = Plugin.objects.get_or_create(meta=meta,
                                                    dock_image='fnndsc/pl-testapp',
                                                    **data)
        #f = ContentFile(self.plg_repr)
        #f.name = self.plugin_name + '.json'
        plugin.save()

        # add plugin's parameters
        parameters = self.plugin_parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=parameters[0]['name'],
            type=parameters[0]['type'],
            flag=parameters[0]['flag'])

        self.pl_manager = manager.PluginManager()

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)

    def test_mananger_can_add_plugin(self):
        """
        Test whether the manager can add a new plugin to the system.
        """
        self.pl_manager.run(['add', 'testapp', self.username, 'http://github.com/repo',
                             'fnndsc/pl-testapp', '--descriptorstring',
                             json.dumps(self.plg_repr)])
        self.assertEqual(Plugin.objects.count(), 2)
        self.assertTrue(PluginParameter.objects.count() > 1)

    def test_mananger_can_modify_plugin(self):
        """
        Test whether the manager can modify an existing plugin.
        """
        # create another chris store user
        user = User.objects.create_user(username='another', email='another@babymri.org',
                                 password='anotherpassword')
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        initial_modification_date = plugin.meta.modification_date
        self.pl_manager.run(['modify', self.plugin_name, 'http://github.com/repo'])
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        self.assertTrue(plugin.meta.modification_date > initial_modification_date)
        self.assertEqual(plugin.meta.public_repo, 'http://github.com/repo')

    def test_mananger_can_remove_plugin(self):
        """
        Test whether the manager can remove an existing plugin from the system.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        self.pl_manager.run(['remove', str(plugin.id)])
        self.assertEqual(Plugin.objects.count(), 0)
        self.assertEqual(PluginParameter.objects.count(), 0)

    def test_mananger_can_get_plugin(self):
        """
        Test whether the manager can return a plugin object.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        self.assertEqual(plugin, self.pl_manager.get_plugin(plugin.id))

    def test_mananger_can_get_plugin_descriptor_file(self):
        """
        Test whether the manager can get a plugin descriptor file from the arguments.
        """
        arg = mock.Mock()
        f = ContentFile(json.dumps(self.plg_repr).encode())
        f.name = self.plugin_name + '.json'
        arg.descriptorfile = f
        self.assertEqual(f, self.pl_manager.get_plugin_descriptor_file(arg))
        arg.descriptorfile = None
        arg.descriptorstring = json.dumps(self.plg_repr)
        arg.name = self.plugin_name + '.json'
        f = self.pl_manager.get_plugin_descriptor_file(arg)
        self.assertEqual(self.plg_repr, json.load(f))
