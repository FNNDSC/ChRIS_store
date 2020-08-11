
import logging

from django.test import TestCase
from django.contrib.auth.models import User


from plugins.models import PluginMeta, Plugin, PluginFilter, PluginParameter


class ModelTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                   'optional': False, 'flag': '--dir', 'short_flag': '-d',
                                   'default': '', 'help': 'test plugin'}]

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
        (plugin, tf) = Plugin.objects.get_or_create(meta=meta, version='0.1' )
        plugin.descriptor_file.name = self.plugin_name + '.json'
        plugin.save()

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)


class PluginMetaModelTests(ModelTests):

    def test_add_owner(self):
        """
        Test whether custom add_owner method adds a new owner to the plugin.
        """
        pl_meta = PluginMeta.objects.get(name=self.plugin_name)
        another_user = User.objects.create_user(username='another',
                                                email='anotherdev@babymri.org',
                                                password='anotherpassword')
        pl_meta.add_owner(another_user)
        self.assertIn(another_user, pl_meta.owner.all())


class PluginModelTests(ModelTests):

    def test_get_plugin_parameter_names(self):
        """
        Test whether custom get_plugin_parameter_names method returns the names of all
        parameters of an existing plugin in a list.
        """
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            action=self.plugin_parameters[0]['action'],
            optional=self.plugin_parameters[0]['optional'],
            flag=self.plugin_parameters[0]['flag'],
            short_flag=self.plugin_parameters[0]['short_flag'],
        )
        param_names = plugin.get_plugin_parameter_names()
        self.assertEqual(param_names, [self.plugin_parameters[0]['name']])


class PluginFilterTests(ModelTests):

    def setUp(self):
        super(PluginFilterTests, self).setUp()
        self.other_plugin_name = "simplefsapp1"
        self.other_plg_repr = self.plg_repr
        self.other_plg_repr['title'] = 'Other Dir plugin'

        user = User.objects.get(username=self.username)

        # create other plugin
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.other_plugin_name)
        meta.owner.set([user])
        Plugin.objects.get_or_create(meta=meta)

    def test_search_name_title_category(self):
        """
        Test whether custom method search_name_title_category returns a filtered queryset
        with all plugins for which name or title or category matches the search value.
        """
        pl1 = Plugin.objects.get(meta__name=self.plugin_name)
        pl1.meta.title = self.plg_repr['title']
        pl1.meta.category = self.plg_repr['category']
        pl1.meta.save()
        pl2 = Plugin.objects.get(meta__name=self.other_plugin_name)
        pl2.meta.title = self.other_plg_repr['title']
        pl2.meta.category = self.other_plg_repr['category']
        pl2.meta.save()
        pl_filter = PluginFilter()
        queryset = Plugin.objects.all()
        qs = pl_filter.search_name_title_category(queryset, 'name_title_category', 'Dir')
        self.assertCountEqual(qs, queryset)
