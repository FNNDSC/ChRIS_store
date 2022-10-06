
import logging
from unittest import mock

from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework import serializers

from plugins.models import PluginMeta, Plugin
from plugins.models import PluginParameter, DefaultIntParameter, DefaultStrParameter
from pipelines.models import Pipeline
from pipelines.serializers import PipelineSerializer


class SerializerTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.plugin_fs_name = "simplefsapp"
        self.plugin_fs_parameters = {'dir': {'type': 'string', 'optional': True,
                                             'default': "./"}}
        self.plugin_ds_name = "simpledsapp"
        self.plugin_ds_parameters = {'dummyInt': {'type': 'integer', 'optional': True,
                                                  'default': 111111}}
        self.username = 'foo'
        self.password = 'foo-pass'

        # create plugins
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_fs_name, type='fs')
        (plugin_fs, tf) = Plugin.objects.get_or_create(meta=meta)
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_ds_name, type='ds')
        (plugin_ds, tf) = Plugin.objects.get_or_create(meta=meta)

        # add plugins' parameters
        (plg_param_fs, tf) = PluginParameter.objects.get_or_create(
            plugin=plugin_fs,
            name='dir',
            type=self.plugin_fs_parameters['dir']['type'],
            optional=self.plugin_fs_parameters['dir']['optional'])
        default = self.plugin_fs_parameters['dir']['default']
        DefaultStrParameter.objects.get_or_create(plugin_param=plg_param_fs,
                                                  value=default)  # set plugin parameter default

        # add a parameter with a default
        (plg_param_ds, tf) = PluginParameter.objects.get_or_create(
            plugin=plugin_ds,
            name='dummyInt',
            type=self.plugin_ds_parameters['dummyInt']['type'],
            optional=self.plugin_ds_parameters['dummyInt']['optional']
        )
        default = self.plugin_ds_parameters['dummyInt']['default']
        DefaultIntParameter.objects.get_or_create(plugin_param=plg_param_ds,
                                                  value=default)  # set plugin parameter default

        # create user
        user = User.objects.create_user(username=self.username, password=self.password)

        # create a pipeline
        self.pipeline_name = 'Pipeline1'
        Pipeline.objects.get_or_create(name=self.pipeline_name, owner=user, category='test')

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)


class PipelineSerializerTests(SerializerTests):

    def setUp(self):
        super(PipelineSerializerTests, self).setUp()

    def test_create(self):
        """
        Test whether overriden 'create' method successfully creates a new pipeline
        with a tree of associated plugins.
        """
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name="mri_analyze", type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)
        owner = User.objects.get(username=self.username)
        plugin_tree = '[{"plugin_id": ' + str(plugin_ds1.id) + \
                         ', "previous_index": null}, {"plugin_id": ' + \
                         str(plugin_ds2.id) + ', "previous_index": 0}]'
        data = {'name': 'Pipeline2', 'plugin_tree': plugin_tree}

        pipeline_serializer = PipelineSerializer(data=data)
        pipeline_serializer.is_valid(raise_exception=True)
        pipeline_serializer.validated_data['owner'] = owner
        pipeline = pipeline_serializer.create(pipeline_serializer.validated_data)
        pipeline_plg_names = [plugin.meta.name for plugin in pipeline.plugins.all()]
        self.assertIn(self.plugin_ds_name, pipeline_plg_names)
        self.assertIn("mri_analyze", pipeline_plg_names)

    def test_update(self):
        """
        Test whether overriden 'update' method successfully updates an existing pipeline
        when 'validated_data' argument contains 'plugin_tree'.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        validated_data = {'name': 'Pipeline2', 'plugin_tree': {'root_index': 0}}
        pipeline_serializer.update(pipeline, validated_data)
        self.assertEqual(pipeline.name, 'Pipeline2')

    def test_validate_validates_required_fields_on_create(self):
        """
        Test whether overriden validate method validates that 'plugin_tree' field
        must be provided when creating a new pipeline.
        """
        owner = User.objects.get(username=self.username)
        data = {'name': 'Pipeline2', 'owner': owner}
        pipeline_serializer = PipelineSerializer(data=data)
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate(data)

    def test_validate_validates_all_defaults_can_be_defined_if_pipeline_unlocked(self):
        """
        Test whether overriden validate method validates that all parameter defaults
        for the pipeline can be defined if the pipeline is unlocked.
        """
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        # add a parameter without a default
        PluginParameter.objects.get_or_create(
            plugin=plugin_ds,
            name='dummyFloat',
            type='float',
            optional=False
        )
        owner = User.objects.get(username=self.username)
        plugin_tree = {'root_index': 0, 'tree': [{'plugin_id': plugin_ds.id,
                                                  'child_indices': [],
                                                  'plugin_parameter_defaults': []}]}
        data = {'name': 'Pipeline2', 'owner': owner, 'plugin_tree': plugin_tree, 'locked': False}
        pipeline_serializer = PipelineSerializer(data=data)
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate(data)

    def test_validate_plugin_tree_is_json_string(self):
        """
        Test whether overriden validate_plugin_tree method validates that the plugin
        tree string is a proper JSON string.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        tree = '[{plugin_id: 8, "previous_index": null}]'
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate_plugin_tree(tree)

    def test_validate_plugin_tree_does_not_contain_empty_list(self):
        """
        Test whether overriden validate_plugin_tree method validates that the plugin
        tree is not an empty list.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        tree = '[]'
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate_plugin_tree(tree)

    def test_validate_plugin_tree_has_plugin_name_and_plugin_version_or_plugin_id(self):
        """
        Test whether overriden validate_plugin_tree method validates that each
        dictionary/node of the plugin tree contains properties plugin_id or plugin_name
        and plugin_version.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        tree = '[{"previous_index": null}]'
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate_plugin_tree(tree)
            tree = '[{"plugin_name": "test", "previous_index": null}]'
            pipeline_serializer.validate_plugin_tree(tree)

    def test_validate_plugin_tree_plugins_exist_and_not_fs(self):
        """
        Test whether overriden validate_plugin_tree method validates that the plugin
        tree contains existing plugins that are not of type 'fs'.
        """
        plugin_fs = Plugin.objects.get(meta__name=self.plugin_fs_name)
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        tree = '[{"plugin_id": ' + str(plugin_fs.id + 100) + ', "previous_index": null}]'
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate_plugin_tree(tree)
        tree = '[{"plugin_id": ' + str(plugin_fs.id) + ', "previous_index": null}]'
        with self.assertRaises(serializers.ValidationError):
            pipeline_serializer.validate_plugin_tree(tree)

    def test_validate_plugin_tree_raises_validation_error_if_get_tree_raises_value_error(self):
        """
        Test whether overriden validate_plugin_tree method raises ValidationError if
        internal call to get_tree method raises ValueError exception.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        tree = '[{"plugin_id": ' + str(plugin_ds.id) + ', "previous_index": null}]'
        with mock.patch('pipelines.serializers.PipelineSerializer.get_tree') as get_tree_mock:
            get_tree_mock.side_effect = ValueError
            with self.assertRaises(serializers.ValidationError):
                pipeline_serializer.validate_plugin_tree(tree)
            get_tree_mock.assert_called_with([{"plugin_id": plugin_ds.id,
                                               "title": plugin_ds.meta.name,
                                               "plugin_parameter_defaults": [],
                                               "previous_index": None}])

    def test_validate_plugin_tree_raises_validation_error_if_validate_tree_raises_value_error(self):
        """
        Test whether overriden validate_plugin_tree method raises ValidationError if
        internal call to validate_tree method raises ValueError exception.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        tree = '[{"plugin_id": ' + str(plugin_ds.id) + ', "previous_index": null}]'
        tree_dict = {'root_index': 0, 'tree': [{"plugin_id": plugin_ds.id, "child_indices": []}]}
        with mock.patch('pipelines.serializers.PipelineSerializer.validate_tree') as validate_tree_mock:
            validate_tree_mock.side_effect = ValueError
            with self.assertRaises(serializers.ValidationError):
                pipeline_serializer.validate_plugin_tree(tree)
                validate_tree_mock.assert_called_with(tree_dict)

    def test_validate_plugin_tree_raises_validation_error_if_title_too_long(self):
        """
        Test whether overriden validate_plugin_tree method raises ValidationError if
        internal call to validate_tree method raises ValueError exception.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        title = 200 * 's'
        tree = '[{"plugin_id": ' + str(plugin_ds.id) + ', "title": ' + title + ', previous_index": null}]'
        tree_dict = {'root_index': 0, 'tree': [{"plugin_id": plugin_ds.id, "title": title, "child_indices": []}]}
        with mock.patch('pipelines.serializers.PipelineSerializer.validate_tree') as validate_tree_mock:
            validate_tree_mock.return_value = None
            with self.assertRaises(serializers.ValidationError):
                pipeline_serializer.validate_plugin_tree(tree)
                validate_tree_mock.assert_called_with(tree_dict)

    def test_validate_plugin_parameter_defaults_raises_validation_error_if_missing_name_or_default(self):
        """
        Test whether custom validate_plugin_parameter_defaults method raises ValidationError if
        'name' or 'default' properties are not included.
        """
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        parameter_defaults = [{'name': 'dummyInt'}]
        with self.assertRaises(serializers.ValidationError):
            PipelineSerializer.validate_plugin_parameter_defaults(plugin_ds, parameter_defaults)
        parameter_defaults = [{'default': 3}]
        with self.assertRaises(serializers.ValidationError):
            PipelineSerializer.validate_plugin_parameter_defaults(plugin_ds, parameter_defaults)
        parameter_defaults = [{'name': 'dummyInt', 'default': 3}]
        PipelineSerializer.validate_plugin_parameter_defaults(plugin_ds, parameter_defaults)

    def test_validate_plugin_parameter_defaults_raises_validation_error_if_parameter_not_found(self):
        """
        Test whether custom validate_plugin_parameter_defaults method raises ValidationError if
        a parameter name is not found.
        """
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        parameter_defaults = [{'name': 'randomInt', 'default': 3}]
        with self.assertRaises(serializers.ValidationError):
            PipelineSerializer.validate_plugin_parameter_defaults(plugin_ds, parameter_defaults)

    def test_validate_plugin_parameter_defaults_raises_validation_error_if_invalid_default_value(self):
        """
        Test whether custom validate_plugin_parameter_defaults method raises ValidationError if
        an invalid default value is provided for a parameter.
        """
        plugin_ds = Plugin.objects.get(meta__name=self.plugin_ds_name)
        parameter_defaults = [{'name': 'dummyInt', 'default': True}]
        with self.assertRaises(serializers.ValidationError):
            PipelineSerializer.validate_plugin_parameter_defaults(plugin_ds, parameter_defaults)

    def test_get_tree(self):
        """
        Test whether custom get_tree method creates a proper dictionary tree from
        a tree list.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name='mri_analyze', type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)

        tree_list = [{"plugin_id": plugin_ds1.id,
                      "title": plugin_ds1.meta.name,
                      "plugin_parameter_defaults": [],
                      "previous_index": None},
                {"plugin_id": plugin_ds2.id,
                 "title": plugin_ds2.meta.name,
                 "plugin_parameter_defaults": [],
                 "previous_index": 0},
                {"plugin_id": plugin_ds1.id,
                 "title": "piping1",
                 "plugin_parameter_defaults": [],
                 "previous_index": 1}]

        tree = [{"plugin_id": plugin_ds1.id,
                 "title": plugin_ds1.meta.name,
                 "plugin_parameter_defaults": [],
                 "child_indices": [1]},
                {"plugin_id": plugin_ds2.id,
                 "title": plugin_ds2.meta.name,
                 "plugin_parameter_defaults": [],
                 "child_indices": [2]},
                {"plugin_id": plugin_ds1.id,
                 "title": "piping1",
                 "plugin_parameter_defaults": [],
                 "child_indices": []}]
        expected_tree_dict = {'root_index': 0, 'tree': tree}

        tree_dict = pipeline_serializer.get_tree(tree_list)
        self.assertEqual(tree_dict, expected_tree_dict)

    def test_get_tree_raises_value_error_if_no_root_found(self):
        """
        Test whether custom get_tree method raises ValueError if the passed tree list
        represents a tree with no root node.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name='mri_analyze', type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)
        tree_list = [{"plugin_id": plugin_ds1.id, "previous_index": 0},
                {"plugin_id": plugin_ds2.id, "previous_index": 0},
                {"plugin_id": plugin_ds1.id, "previous_index": 1}]
        with self.assertRaises(ValueError):
            pipeline_serializer.get_tree(tree_list)

    def test_get_tree_raises_value_error_if_it_finds_invalid_previous_index(self):
        """
        Test whether custom get_tree method raises TypeError if the passed tree list
        has a node with None as previous index for a node that is not the root.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name='mri_analyze', type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)

        tree_list = [{"plugin_id": plugin_ds1.id,
                      "title": plugin_ds1.meta.name,
                      "plugin_parameter_defaults": [],
                      "previous_index": None},
                {"plugin_id": plugin_ds2.id,
                 "title": plugin_ds2.meta.name,
                 "plugin_parameter_defaults": [],
                 "previous_index": 0},
                {"plugin_id": plugin_ds1.id,
                 "title": "piping1",
                 "plugin_parameter_defaults": [],
                 "previous_index": None}]
        with self.assertRaises(ValueError):
            pipeline_serializer.get_tree(tree_list)

        tree_list = [{"plugin_id": plugin_ds1.id,
                      "title": plugin_ds1.meta.name,
                      "plugin_parameter_defaults": [],
                      "previous_index": None},
                {"plugin_id": plugin_ds2.id,
                 "title": plugin_ds2.meta.name,
                 "plugin_parameter_defaults": [],
                 "previous_index": 3},
                {"plugin_id": plugin_ds1.id,
                 "title": "piping1",
                 "plugin_parameter_defaults": [],
                 "previous_index": 1}]
        with self.assertRaises(ValueError):
            pipeline_serializer.get_tree(tree_list)

    def test_validate_tree(self):
        """
        Test whether custom validate_tree method raises ValueError if the passed
        dictionary represents a tree that is not connected.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name='mri_analyze', type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)
        tree = [{"plugin_id": plugin_ds1.id, "child_indices": []},
                {"plugin_id": plugin_ds2.id, "child_indices": [2]},
                {"plugin_id": plugin_ds1.id, "child_indices": [1]}]
        tree_dict = {'root_index': 0, 'tree': tree}
        with self.assertRaises(ValueError):
            pipeline_serializer.validate_tree(tree_dict)

    def test__add_plugin_tree_to_pipeline(self):
        """
        Test whether custom internal _add_plugin_tree_to_pipeline method properly
        associates a tree of plugins to a pipeline in the DB.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pipeline_serializer = PipelineSerializer(pipeline)
        plugin_ds1 = Plugin.objects.get(meta__name=self.plugin_ds_name)
        (meta, tf) = PluginMeta.objects.get_or_create(name='mri_analyze', type='ds')
        (plugin_ds2, tf) = Plugin.objects.get_or_create(meta=meta)

        tree = [{"plugin_id": plugin_ds1.id,
                 "title": plugin_ds1.meta.name,
                 "plugin_parameter_defaults": [],
                 "child_indices": [1]},
                {"plugin_id": plugin_ds2.id,
                 "title": "piping2",
                 "plugin_parameter_defaults": [],
                 "child_indices": [2]},
                {"plugin_id": plugin_ds1.id,
                 "title": "piping1",
                 "plugin_parameter_defaults": [],
                 "child_indices": []}]
        tree_dict = {'root_index': 0, 'tree': tree}

        pipeline_serializer._add_plugin_tree_to_pipeline(pipeline, tree_dict)
        pipeline_plg_names = [plugin.meta.name for plugin in pipeline.plugins.all()]
        self.assertEqual(len(pipeline_plg_names), 3)
        self.assertEqual(len([name for name in pipeline_plg_names if name == self.plugin_ds_name]), 2)
