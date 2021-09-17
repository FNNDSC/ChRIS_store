
import logging
import json
import io
from unittest import mock

from django.test import TestCase, tag
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.base import ContentFile

from rest_framework import status

from plugins.models import (PluginMeta, PluginMetaStar, PluginMetaCollaborator, Plugin,
                            PluginParameter)


class ViewTests(TestCase):
    
    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.username = 'foo'
        self.password = 'foopassword'
        self.email = 'dev@babymri.org'
        self.plugin_name = 'simplefsapp'
        self.plugin_version = '0.1'
        self.content_type = 'application/vnd.collection+json'

        plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                              'optional': True, 'flag': '--dir', 'short_flag': '-d',
                              'default': '/', 'help': 'test plugin', 'ui_exposed': True}]

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
        self.plg_repr['parameters'] = plugin_parameters

        # create basic models

        # create a chris store user
        user = User.objects.create_user(username=self.username, email=self.email,
                                        password=self.password)
        # create a plugin
        (pl_meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name,
                                                         type='fs',
                                                         title='chris app',
                                                         public_repo='http://gitgub.com')
        PluginMetaCollaborator.objects.create(meta=pl_meta, user=user)
        (plugin, tf) = Plugin.objects.get_or_create(meta=pl_meta,
                                                    version=self.plugin_version,
                                                    dock_image='fnndsc/pl-testapp')
        plugin.descriptor_file.name = self.plugin_name + '.json'
        plugin.save()

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)


class PluginMetaListViewTests(ViewTests):
    """
    Test the pluginmeta-list view.
    """

    def setUp(self):
        super(PluginMetaListViewTests, self).setUp()
        self.read_url = reverse("pluginmeta-list")

    def test_plugin_meta_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_list_success_unauthenticated(self):
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_name)


class PluginMetaDetailViewTests(ViewTests):
    """
    Test the pluginmeta-detail view.
    """

    def setUp(self):
        super(PluginMetaDetailViewTests, self).setUp()

        meta = PluginMeta.objects.get(name=self.plugin_name)
        self.read_update_delete_url = reverse("pluginmeta-detail", kwargs={"pk": meta.id})

        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')

    def test_plugin_meta_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_update_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_detail_success_unauthenticated(self):
        response = self.client.get(self.read_update_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_update_success(self):
        put = json.dumps({
            "template": {"data": [{"name": "public_repo", "value": "http://localhost11.com"}]}})
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(self.read_update_delete_url, data=put,
                                   content_type=self.content_type)
        self.assertContains(response, "http://localhost11")

    def test_plugin_meta_update_failure_unauthenticated(self):
        response = self.client.put(self.read_update_delete_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_update_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.put(self.read_update_delete_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_plugin_meta_delete_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PluginMeta.objects.count(), 0)
        self.assertEqual(Plugin.objects.count(), 0)

    def test_plugin_meta_delete_failure_unauthenticated(self):
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_delete_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PluginMetaListQuerySearchViewTests(ViewTests):
    """
    Test the plugin-list-query-search view.
    """

    def setUp(self):
        super(PluginMetaListQuerySearchViewTests, self).setUp()
        self.list_url = reverse("pluginmeta-list-query-search") + '?name=' + self.plugin_name

    def test_plugin_meta_list_query_search_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_list_query_search_success_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_list_query_search_across_name_title_category_success(self):
        search_params = '?name_title_category=chris'
        list_url = reverse("plugin-list-query-search") + search_params
        response = self.client.get(list_url)
        self.assertContains(response, 'chris app')


class PluginMetaStarListViewTests(ViewTests):
    """
    Test the pluginmetastar-list view.
    """

    def setUp(self):
        super(PluginMetaStarListViewTests, self).setUp()
        self.create_read_url = reverse("pluginmetastar-list")
        self.post = json.dumps({"template": {"data": [{"name": "plugin_name",
                                                       "value": self.plugin_name}]}})

    def test_plugin_meta_star_create_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_plugin_meta_star_create_failure_unauthenticated(self):
        response = self.client.post(self.create_read_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_star_list_success_authenticated(self):
        user = User.objects.create_user(username='bob', email='bob@test.com',
                                        password='bobpassword')
        # create a plugin meta
        (meta, tf) = PluginMeta.objects.get_or_create(name='testplugin')
        PluginMetaCollaborator.objects.create(meta=meta, user=user)
        PluginMetaStar.objects.get_or_create(user=user, meta=meta)

        meta = PluginMeta.objects.get(name=self.plugin_name)
        user = User.objects.get(username=self.username)
        PluginMetaStar.objects.get_or_create(user=user, meta=meta)

        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.create_read_url)
        self.assertContains(response, self.plugin_name)
        self.assertNotContains(response, 'testplugin')

    def test_plugin_meta_star_list_failure_unauthenticated(self):
        response = self.client.get(self.create_read_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PluginMetaStarDetailViewTests(ViewTests):
    """
    Test the pluginmetastar-detail view.
    """

    def setUp(self):
        super(PluginMetaStarDetailViewTests, self).setUp()

        meta = PluginMeta.objects.get(name=self.plugin_name)
        user = User.objects.get(username=self.username)
        star, tf = PluginMetaStar.objects.get_or_create(user=user, meta=meta)

        self.read_delete_url = reverse("pluginmetastar-detail", kwargs={"pk": star.id})

        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')

    def test_plugin_meta_star_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_star_detail_failure_unauthenticated(self):
        response = self.client.get(self.read_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_star_delete_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(self.read_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PluginMetaStar.objects.count(), 0)

    def test_plugin_meta_star_delete_failure_unauthenticated(self):
        response = self.client.delete(self.read_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_star_delete_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.delete(self.read_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PluginMetaCollaboratorListViewTests(ViewTests):
    """
    Test the pluginmeta-pluginmetacollaborator-list view.
    """

    def setUp(self):
        super(PluginMetaCollaboratorListViewTests, self).setUp()

        meta = PluginMeta.objects.get(name=self.plugin_name)
        self.create_read_url = reverse("pluginmeta-pluginmetacollaborator-list",
                                       kwargs={"pk": meta.id})
        self.post = json.dumps({"template": {"data": [{"name": "username",
                                                       "value": 'another'},
                                                      {"name": "role",
                                                       "value": 'M'}]}})
        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')

    def test_plugin_meta_collaborator_create_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_plugin_meta_collaborator_create_failure_unauthenticated(self):
        response = self.client.post(self.create_read_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_collaborator_create_failure_missing_username(self):
        post = json.dumps({"template": {"data": [{"name": "role", "value": 'M'}]}})
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_meta_collaborator_create_failure_recreating_itself(self):
        post = json.dumps({"template": {"data": [{"name": "username",
                                                  "value": self.username},
                                                 {"name": "role",
                                                  "value": 'M'}]}})
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_meta_collaborator_list_success_authenticated(self):
        User.objects.create_user(username='bob', email='bob@test.com',
                                 password='bobpassword')
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.create_read_url)
        self.assertContains(response, self.username)
        self.assertNotContains(response, 'bob')

    def test_plugin_meta_collaborator_list_failure_unauthenticated(self):
        response = self.client.get(self.create_read_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PluginMetaCollaboratorDetailViewTests(ViewTests):
    """
    Test the pluginmetacollaborator-detail view.
    """

    def setUp(self):
        super(PluginMetaCollaboratorDetailViewTests, self).setUp()

        meta = PluginMeta.objects.get(name=self.plugin_name)
        collab = PluginMetaCollaborator.objects.get(meta=meta)
        self.read_update_delete_url = reverse("pluginmetacollaborator-detail",
                                              kwargs={"pk": collab.id})

        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')

    def test_plugin_meta_collaborator_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_update_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_meta_collaborator_detail__failure_unauthenticated(self):
        response = self.client.get(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_collaborator_update_success(self):
        meta = PluginMeta.objects.get(name=self.plugin_name)
        user = User.objects.get(username='another')
        PluginMetaCollaborator.objects.create(meta=meta, user=user)
        put = json.dumps({
            "template": {"data": [{"name": "role", "value": "M"}]}})
        self.client.login(username='another', password='another-pass')
        response = self.client.put(self.read_update_delete_url, data=put,
                                   content_type=self.content_type)
        self.assertContains(response, "M")

    def test_plugin_meta_collaborator_update_failure_unauthenticated(self):
        response = self.client.put(self.read_update_delete_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_collaborator_update_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.put(self.read_update_delete_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_plugin_meta_collaborator_update_failure_updating_itself(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(self.read_update_delete_url, data={},
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_plugin_meta_collaborator_delete_success(self):
        meta = PluginMeta.objects.get(name=self.plugin_name)
        user = User.objects.get(username='another')
        PluginMetaCollaborator.objects.create(meta=meta, user=user)
        self.client.login(username='another', password='another-pass')
        self.assertEqual(PluginMetaCollaborator.objects.count(), 2)
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PluginMetaCollaborator.objects.count(), 1)

    def test_plugin_meta_collaborator_delete_failure_unauthenticated(self):
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_meta_collaborator_delete_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_plugin_meta_collaborator_delete_failure_deleting_itself(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PluginListViewTests(ViewTests):
    """
    Test the plugin-list view.
    """

    def setUp(self):
        super(PluginListViewTests, self).setUp()
        self.create_read_url = reverse("plugin-list")
        self.post = {"descriptor_file": "", "name": self.plugin_name,
                     "public_repo": "http://localhost", "dock_image": "pl-testplugin"}

    @tag('integration')
    def test_integration_plugin_create_success(self):
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            post = self.post.copy()
            post['name'] = 'testplugin'
            post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            #  multipart request
            response = self.client.post(self.create_read_url, data=post)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_plugin_create_failure_name_version_combination_already_exists(self):
        self.plg_repr['version'] = self.plugin_version
        with io.StringIO(json.dumps(self.plg_repr)) as f:
            self.post["descriptor_file"] = f
            self.client.login(username=self.username, password=self.password)
            response = self.client.post(self.create_read_url, data=self.post)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_plugin_create_failure_missing_descriptor_file(self):
        post = json.dumps({
            "template": {"data": [{"name": "name", "value": "testplugin"},
                                  {"name": "public_repo", "value": "http://localhost.com"},
                                  {"name": "dock_image", "value": "pl-testplugin"}]}})
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(self.create_read_url, data=post,
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

    def test_plugin_create_failure_unauthenticated(self):
        response = self.client.post(self.create_read_url, data={})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.create_read_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_list_success_unauthenticated(self):
        response = self.client.get(self.create_read_url)
        self.assertContains(response, self.plugin_name)


class PluginDetailViewTests(ViewTests):
    """
    Test the plugin-detail view.
    """

    def setUp(self):
        super(PluginDetailViewTests, self).setUp()

        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        self.read_update_delete_url = reverse("plugin-detail", kwargs={"pk": plugin.id})

        # create another chris store user
        User.objects.create_user(username='another', email='another@babymri.org',
                                 password='another-pass')

    def test_plugin_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_update_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_detail_success_unauthenticated(self):
        response = self.client.get(self.read_update_delete_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_delete_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Plugin.objects.count(), 0)

    def test_plugin_delete_failure_unauthenticated(self):
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_plugin_delete_failure_access_denied(self):
        self.client.login(username='another', password='another-pass')
        response = self.client.delete(self.read_update_delete_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PluginListQuerySearchViewTests(ViewTests):
    """
    Test the plugin-list-query-search view.
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
        search_params = '?name_title_category=chris'
        list_url = reverse("plugin-list-query-search") + search_params
        response = self.client.get(list_url)
        self.assertContains(response, 'chris app')


class PluginParameterListViewTests(ViewTests):
    """
    Test the pluginparameter-list view.
    """

    def setUp(self):
        super(PluginParameterListViewTests, self).setUp()
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                   'optional': False, 'flag': '--dir', 'short_flag': '-d',
                                   'default': '', 'help': 'test plugin'}]
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        self.list_url = reverse("pluginparameter-list", kwargs={"pk": plugin.id})

        # add plugin's parameters
        PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            action=self.plugin_parameters[0]['action'],
            flag=self.plugin_parameters[0]['flag'],
            short_flag=self.plugin_parameters[0]['short_flag'],
            optional=self.plugin_parameters[0]['optional']
        )

    def test_plugin_parameter_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])

    def test_plugin_parameter_list_success_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])


class PluginParameterDetailViewTests(ViewTests):
    """
    Test the pluginparameter-detail view.
    """

    def setUp(self):
        super(PluginParameterDetailViewTests, self).setUp()
        self.plugin_parameters = [{'name': 'dir', 'type': str.__name__, 'action': 'store',
                                   'optional': False, 'flag': '--dir', 'short_flag': '-d',
                                   'default': '', 'help': 'test plugin'}]
        plugin = Plugin.objects.get(meta__name=self.plugin_name)
        # create a plugin parameter
        (param, tf) = PluginParameter.objects.get_or_create(
            plugin=plugin,
            name=self.plugin_parameters[0]['name'],
            type=self.plugin_parameters[0]['type'],
            action=self.plugin_parameters[0]['action'],
            flag=self.plugin_parameters[0]['flag'],
            short_flag=self.plugin_parameters[0]['short_flag'],
            optional=self.plugin_parameters[0]['optional']
        )

        self.read_url = reverse("pluginparameter-detail", kwargs={"pk": param.id})

    def test_plugin_parameter_detail_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])

    def test_plugin_parameter_detail_success_unauthenticated(self):
        response = self.client.get(self.read_url)
        self.assertContains(response, self.plugin_parameters[0]['name'])
