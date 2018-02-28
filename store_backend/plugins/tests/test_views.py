
import json
import io
from unittest import mock

from django.test import TestCase, tag
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings

from rest_framework import status

from plugins.models import Plugin, PluginParameter
from plugins.services.manager import PluginManager
from plugins import views

class ViewTests(TestCase):
    
    def setUp(self):
        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = "simplefsapp"
        self.content_type = 'application/vnd.collection+json'

        # create basic models

        # create a chris store user
        user = User.objects.create_user(username=self.username, email=self.email,
                                 password=self.password)
        # create a plugin
        Plugin.objects.get_or_create(name=self.plugin_name, type='fs', owner=user)


class PluginListViewTests(ViewTests):
    """
    Test the plugin-list view
    """

    def setUp(self):
        super(PluginListViewTests, self).setUp()
        self.create_read_url = reverse("plugin-list")

    @tag('integration')
    def test_integration_plugin_create_success(self):

        plugin_parameters = [{'name': 'dir', 'type': str.__name__,
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        plg_repr = {}
        plg_repr['name'] = self.plugin_name
        plg_repr['type'] = 'fs'
        plg_repr['authors'] = 'DEV FNNDSC'
        plg_repr['title'] = 'Dir plugin'
        plg_repr['description'] = 'Dir test plugin'
        plg_repr['license'] = 'MIT'
        plg_repr['version'] = 'v0.1'
        plg_repr['execshell'] = 'python3'
        plg_repr['selfpath'] = '/usr/src/simplefsapp'
        plg_repr['selfexec'] = 'simplefsapp.py'
        plg_repr['parameters'] = plugin_parameters

        self.client.login(username=self.username, password=self.password)
        with io.StringIO(json.dumps(plg_repr)) as f:
            post = {"descriptor_file": f, "name": "testplugin",
                    "public_repo": "http://localhost", "dock_image": "pl-testplugin"}
            response = self.client.post(self.create_read_url, data=post)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_plugin_create_failure_unauthenticated(self):
        response = self.client.post(self.create_read_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_create_failure_missing_descriptor_file(self):
        self.client.login(username=self.username, password=self.password)
        post = { "name": "testplugin", "public_repo": "http://localhost",
                 "dock_image": "pl-testplugin"}
        response = self.client.post(self.create_read_url, data=post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_missing_public_repo(self):
        self.client.login(username=self.username, password=self.password)
        post = { "name": "testplugin", "descriptor_file": io.StringIO("file content"),
                 "dock_image": "pl-testplugin"}
        response = self.client.post(self.create_read_url, data=post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_missing_dock_image(self):
        self.client.login(username=self.username, password=self.password)
        post = { "name": "testplugin", "descriptor_file": io.StringIO("file content"),
                 "public_repo": "http://localhost"}
        response = self.client.post(self.create_read_url, data=post)
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

        plugin_parameters = [{'name': 'dir', 'type': str.__name__,
                                      'optional': False, 'flag':'--dir', 'default': '',
                                      'help': 'test plugin'}]
        plg_repr = {}
        plg_repr['name'] = self.plugin_name
        plg_repr['type'] = 'fs'
        plg_repr['authors'] = 'DEV FNNDSC'
        plg_repr['title'] = 'Dir plugin'
        plg_repr['description'] = 'Dir test plugin'
        plg_repr['license'] = 'MIT'
        plg_repr['version'] = 'v0.1'
        plg_repr['execshell'] = 'python3'
        plg_repr['selfpath'] = '/usr/src/simplefsapp'
        plg_repr['selfexec'] = 'simplefsapp.py'
        plg_repr['parameters'] = plugin_parameters

        self.client.login(username=self.username, password=self.password)
        with io.StringIO(json.dumps(plg_repr)) as f:
            put = {"descriptor_file": f, "public_repo": "http://localhost",
                   "dock_image": "fnndsc-pl-testplugin"}
        response = self.client.put(self.read_update_url, data=put,
                                   content_type='multipart/form-data')
        import pdb; pdb.set_trace()
        self.assertContains(response, "fnndsc-pl-testplugin")
        self.assertContains(response, self.plugin_name)

    def test_plugin_update_failure_unauthenticated(self):
        response = self.client.put(self.read_update_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_update_failure_access_denied(self):
        # create another chris store user
        user = User.objects.create_user(username='another', email='another@babymri.org',
                                        password='anotherpassword')
        self.client.login(username='another', password='anotherpassword')
        response = self.client.put(self.read_update_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)