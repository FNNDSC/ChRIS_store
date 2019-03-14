
from django.test import TestCase
from django.contrib.auth.models import User


from plugins.models import Plugin, PluginFilter, PluginParameter


class ModelTests(TestCase):

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
        self.plg_repr['icon'] = 'http://github.com/plugin'
        self.plg_repr['authors'] = 'DEV FNNDSC'
        self.plg_repr['title'] = 'Dir plugin'
        self.plg_repr['category'] = 'Dir'
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
        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name, version='0.1')
        plugin.owner.set([user])


class PluginModelTests(ModelTests):

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
        self.assertEqual(param_names, [self.plugin_parameters[0]['name']])

    def test_add_owner(self):
        """
        Test whether custom add_owner method can add a new owner to a plugin and all
        its versions.
        """
        plugin_v1 = Plugin.objects.get(name=self.plugin_name)
        (plugin_v2, tf) = Plugin.objects.get_or_create(name=self.plugin_name, version='0.2')
        user1 = User.objects.get(username=self.username)
        plugin_v2.owner.set([user1])
        user2 = User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')
        plugin_v2.add_owner(user2)
        plugin_v1_owners = plugin_v1.owner.all()
        plugin_v2_owners = plugin_v2.owner.all()
        self.assertIn(user1, plugin_v1_owners)
        self.assertIn(user2, plugin_v2_owners)
        self.assertIn(user1, plugin_v1_owners)
        self.assertIn(user2, plugin_v2_owners)


class PluginFilterTests(ModelTests):

    def setUp(self):
        super(PluginFilterTests, self).setUp()
        self.other_plugin_name = "simplefsapp1"
        self.other_plg_repr = self.plg_repr
        self.other_plg_repr['title'] = 'Other Dir plugin'

        user = User.objects.get(username=self.username)

        # create other plugin
        (plugin, tf) = Plugin.objects.get_or_create(name=self.other_plugin_name)
        plugin.owner.set([user])

    def test_search_name_title_category(self):
        """
        Test whether custom method search_name_title_category returns a filtered queryset
        with all plugins for which name or title or category matches the search value.
        """
        pl1 = Plugin.objects.get(name=self.plugin_name)
        pl1.title = self.plg_repr['title']
        pl1.category = self.plg_repr['category']
        pl1.save()
        pl2 = Plugin.objects.get(name=self.other_plugin_name)
        pl2.title = self.other_plg_repr['title']
        pl2.category = self.other_plg_repr['category']
        pl2.save()
        pl_filter = PluginFilter()
        queryset = Plugin.objects.all()
        qs = pl_filter.search_name_title_category(queryset, 'name_title_category', 'Dir')
        self.assertCountEqual(qs, queryset)