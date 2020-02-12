
import logging

from django.test import TestCase
from django.contrib.auth.models import User

from plugins.models import Plugin
from plugins.models import PluginParameter, DefaultIntParameter
from pipelines.models import Pipeline
from pipelines.models import PluginPiping
from pipelines.models import DEFAULT_PIPING_PARAMETER_MODELS


class ModelTests(TestCase):

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.CRITICAL)

        self.plugin_ds_name = "simpledsapp"
        self.plugin_ds_parameters = {'prefix': {'type': 'string', 'optional': False}}
        self.username = 'foo'
        self.password = 'foo-pass'

        # create plugin
        (plugin_ds, tf) = Plugin.objects.get_or_create(name=self.plugin_ds_name,
                                                       type='ds')
        # add plugin's parameters
        (plg_param_ds, tf)= PluginParameter.objects.get_or_create(
            plugin=plugin_ds,
            name='prefix',
            type=self.plugin_ds_parameters['prefix']['type'],
            optional=self.plugin_ds_parameters['prefix']['optional']) # this plugin parameter has no default

        # create user
        user = User.objects.create_user(username=self.username, password=self.password)

        # create a pipeline
        self.pipeline_name = 'Pipeline1'
        (pipeline, tf) = Pipeline.objects.get_or_create(name=self.pipeline_name, owner=user)

        # create two plugin pipings
        self.pips = []
        (pip, tf) = PluginPiping.objects.get_or_create(plugin=plugin_ds, pipeline=pipeline)
        self.pips.append(pip)
        (pip, tf) = PluginPiping.objects.get_or_create(plugin=plugin_ds, previous=pip,
                                                        pipeline=pipeline)
        self.pips.append(pip)

        # create default values for the piping parameters as the corresponding plugin
        # didn't set a default
        param_type = self.plugin_ds_parameters['prefix']['type']
        default_model_class = DEFAULT_PIPING_PARAMETER_MODELS[param_type]
        for i in range(2):
            (default_piping_param, tf) = default_model_class.objects.get_or_create(
                plugin_piping=self.pips[i], plugin_param=plg_param_ds)
            default_piping_param.value = "test" + str(i)
            default_piping_param.save()

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.DEBUG)


class PipelineModelTests(ModelTests):

    def test_check_parameter_defaults(self):
        """
        Test whether custom check_parameter_defaults method raises an exception if
        any of the plugin parameters associated to any of the pipings in the pipeline
        doesn't have a default value.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        plugin_ds = Plugin.objects.get(name=self.plugin_ds_name)
        # add a new plugin piping to pipeline but do not set a default value for
        # the plugin parameter
        PluginPiping.objects.get_or_create(plugin=plugin_ds, pipeline=pipeline,
                                           previous=self.pips[1])
        with self.assertRaises(ValueError):
            pipeline.check_parameter_defaults()

    def test_get_accesible_pipelines(self):
        """
        Test whether custom get_accesible_pipelines method returns a filtered queryset
        with all the pipelines that are accessible to a given user (not locked or
        otherwise own by the user).
        """
        user1 = User.objects.get(username=self.username)
        # create new user
        user2 = User.objects.create_user(username='testuser', password='testuser-pass')
        accessible_pipelines_user1 = Pipeline.get_accesible_pipelines(user1)
        self.assertEqual(len(accessible_pipelines_user1),1)
        self.assertEqual(accessible_pipelines_user1[0], Pipeline.objects.all()[0])
        self.assertEqual(len(Pipeline.get_accesible_pipelines(user2)), 0)


class PluginPipingModelTests(ModelTests):

    def test_save(self):
        """
        Test whether overriden save method saves the default plugin parameters' values
        associated with this piping.
        """
        plugin_ds = Plugin.objects.get(name=self.plugin_ds_name)
        # add a parameter with a default
        (plg_param_ds, tf)= PluginParameter.objects.get_or_create(
            plugin=plugin_ds,
            name='dummyInt',
            type='integer',
            optional=True
        )
        DefaultIntParameter.objects.get_or_create(plugin_param=plg_param_ds, value=1)  # set plugin parameter default
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        pip = PluginPiping()
        pip.plugin = plugin_ds
        pip.pipeline = pipeline
        pip.save()
        defaults = pip.integer_param.all()
        self.assertEqual(len(defaults), 1)
        self.assertEqual(defaults[0].value, 1)
        pip.save(parameter_defaults=[{'name': 'dummyInt', 'default': 2}])
        defaults = pip.integer_param.all()
        self.assertEqual(defaults[0].value, 2)

    def test_check_parameter_defaults(self):
        """
        Test whether custom check_parameter_defaults method raises an exception if
        any of the plugin parameters associated to the piping doesn't have a default value.
        """
        pipeline = Pipeline.objects.get(name=self.pipeline_name)
        plugin_ds = Plugin.objects.get(name=self.plugin_ds_name)
        # add a new plugin piping to pipeline but do not set a default value for
        # the plugin parameter
        (pip, tf) = PluginPiping.objects.get_or_create(plugin=plugin_ds, pipeline=pipeline,
                                           previous=self.pips[1])
        with self.assertRaises(ValueError):
            pip.check_parameter_defaults()
