
import json
import io
from unittest import mock

from django.test import TestCase, tag
from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework import status

from plugins.models import Plugin, PluginParameter


class ViewTests(TestCase):
    
    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = 'simplefsapp'
        self.content_type = 'application/vnd.collection+json'

        plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                      'optional': True, 'flag':'--dir', 'default': './',
                                      'help': 'test plugin'}]
        plg_repr = {}
        plg_repr['type'] = 'fs'
        plg_repr['icon'] = 'http://github.com/plugin'
        plg_repr['authors'] = 'DEV FNNDSC'
        plg_repr['title'] = 'Dir plugin'
        plg_repr['description'] = 'Dir test plugin'
        plg_repr['license'] = 'MIT'
        plg_repr['version'] = 'v0.1'
        plg_repr['execshell'] = 'python3'
        plg_repr['selfpath'] = '/usr/src/simplefsapp'
        plg_repr['selfexec'] = 'simplefsapp.py'
        plg_repr['parameters'] = plugin_parameters
        self.plg_repr = plg_repr

        # create basic models

        # create a chris store user
        user = User.objects.create_user(username=self.username, email=self.email,
                                 password=self.password)
        # create a plugin
        (plugin, tf) = Plugin.objects.get_or_create(name=self.plugin_name, version='v0.1',
                                                    title='chris app', type='fs')
        plugin.owner.set([user])


class PluginListViewTests(ViewTests):
    """
    Test the plugin-list view
    """

    def setUp(self):
        super(PluginListViewTests, self).setUp()
        self.list_url = reverse("plugin-list")

    def test_plugin_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)
        self.assertContains(response, 'user_plugins')

    def test_plugin_list_success_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)
        self.assertNotContains(response, 'user_plugins')


class UserPluginListViewTests(ViewTests):
    """
    Test the user-plugin-list view
    """

    def setUp(self):
        super(UserPluginListViewTests, self).setUp()
        self.create_read_url = reverse("user-plugin-list")
        self.post = {"descriptor_file": "", "name": "testplugin",
                     "public_repo": "http://localhost", "dock_image": "pl-testplugin"}

    @tag('integration')
    def test_integration_plugin_create_success(self):
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            self.post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            #  multipart request
            response = self.client.post(self.create_read_url, data=self.post)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_plugin_create_failure_unauthenticated(self):
        response = self.client.post(self.create_read_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_create_failure_missing_descriptor_file(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_missing_public_repo(self):
        del self.post["public_repo"]
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            self.post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            response = self.client.post(self.create_read_url, data=self.post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_missing_dock_image(self):
        del self.post["dock_image"]
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            self.post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            response = self.client.post(self.create_read_url, data=self.post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_name_version_combination_already_exists(self):
        self.post["name"] = self.plugin_name
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            self.post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            response = self.client.post(self.create_read_url, data=self.post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_list_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.create_read_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_list_failure_unauthenticated(self):
        response = self.client.get(self.create_read_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PluginDetailViewTests(ViewTests):
    """
    Test the plugin-detail view
    """

    def setUp(self):
        super(PluginDetailViewTests, self).setUp()

        plugin = Plugin.objects.get(name=self.plugin_name)
        self.read_update_url = reverse("plugin-detail", kwargs={"pk": plugin.id})

    def test_plugin_detail_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_update_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_detail_failure_unauthenticated(self):
        response = self.client.get(self.read_update_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_update_success(self):
        pass # self.client limited as it doesn't support multipart data on PUT requests

    def test_plugin_update_failure_unauthenticated(self):
        response = self.client.put(self.read_update_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_update_failure_access_denied(self):
        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='anotherpassword')
        self.client.login(username='another', password='anotherpassword')
        response = self.client.put(self.read_update_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PluginListQuerySearchViewTests(ViewTests):
    """
    Test the plugin-list-query-search view
    """

    def setUp(self):
        super(PluginListQuerySearchViewTests, self).setUp()
        self.list_url = reverse("plugin-list-query-search") + '?name=' + self.plugin_name

    def test_plugin_list_query_search_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_list_query_search_success_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_list_query_search_across_name_title_category_success(self):
        search_params = '?name=chris&title=chris&category=chris'
        list_url = reverse("plugin-list-query-search") + search_params
        response = self.client.get(list_url)
        self.assertContains(response, 'chris')



class PluginParameterListViewTests(ViewTests):
    """
    Test the pluginparameter-list view
    """

    def setUp(self):
        super(PluginParameterListViewTests, self).setUp()
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        plugin = Plugin.objects.get(name=self.plugin_name)
        self.list_url = reverse("pluginparameter-list", kwargs={"pk": plugin.id})

        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            action=self.plugin_parameters[0]['action'],
            flag=self.plugin_parameters[0]['flag'],
            optional=self.plugin_parameters[0]['optional'])

    def test_plugin_parameter_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])

    def test_plugin_parameter_list_success_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])


class PluginParameterDetailViewTests(ViewTests):
    """
    Test the pluginparameter-detail view
    """

    def setUp(self):
        super(PluginParameterDetailViewTests, self).setUp()
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        plugin = Plugin.objects.get(name=self.plugin_name)
        # create a plugin parameter
        (param, tf) = PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            action=self.plugin_parameters[0]['action'],
            flag=self.plugin_parameters[0]['flag'],
            optional=self.plugin_parameters[0]['optional'])

        self.read_url = reverse("pluginparameter-detail", kwargs={"pk": param.id})

    def test_plugin_parameter_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])

    def test_plugin_parameter_detail_success_unauthenticated(self):
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])
