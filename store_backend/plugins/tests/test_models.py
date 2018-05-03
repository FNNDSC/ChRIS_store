
from django.test import TestCase
from django.contrib.auth.models import User


from plugins.models import Plugin, PluginParameter

class PluginModelTests(TestCase):
    
    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
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
            action=self.plugin_parameters[0]['action'],
            optional=self.plugin_parameters[0]['optional'],
            flag=self.plugin_parameters[0]['flag'])
        param_names = plugin.get_plugin_parameter_names()
        self.assertEquals(param_names, [self.plugin_parameters[0]['name']])