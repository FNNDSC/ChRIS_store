"""
Plugin manager module that provides functionality to add, modify and delete plugins to the
plugins django app.
"""

import os
import sys
import json
import docker
from argparse import ArgumentParser

if "DJANGO_SETTINGS_MODULE" not in os.environ:
    # django needs to be loaded (eg. when this script is run from the command line)
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django
    django.setup()

from django.utils import timezone
from plugins.models import Plugin, PluginParameter, TYPES, PLUGIN_TYPE_CHOICES


class PluginManager(object):

    def __init__(self):
        parser = ArgumentParser(description='Manage plugins')
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--add", help="add a new plugin", metavar='DockImage')
        group.add_argument("-r", "--remove", help="remove an existing plugin",
                           metavar='PluginName')
        group.add_argument("-m", "--modify", help="register NOW as modification date",
                           metavar='DockImage')
        self.parser = parser

    def get_plugin_app_representation(self, dock_image_name):
        """
        Get a plugin app representation given its docker image name.
        """
        client = docker.from_env()
        # first try to pull the latest image
        try:
            img = client.images.pull(dock_image_name)
        except docker.errors.APIError:
            # use local image ('remove' option automatically removes container when finished)
            byte_str = client.containers.run(dock_image_name, remove=True)
        else:
            byte_str = client.containers.run(img, remove=True)
        app_repr = json.loads(byte_str.decode())
        plugin_types = [plg_type[0] for plg_type in PLUGIN_TYPE_CHOICES]
        if app_repr['type'] not in plugin_types:
            raise ValueError("A plugin's TYPE can only be any of %s. Please fix it in %s"
                             % (plugin_types, dock_image_name))
        return app_repr

    def get_plugin_name(self, app_repr):
        """
        Get a plugin app's name from the plugin app's representation.
        """
        # the plugin app exec name stored in 'selfexec' must be: 'plugin name' + '.py'
        if 'selfexec' not in app_repr:
            raise KeyError("Missing 'selfexec' from plugin app's representation")
        return app_repr['selfexec'].rsplit( ".", 1 )[ 0 ]

    def _save_plugin_param(self, plugin, param):
        """
        Internal method to save a plugin parameter into the DB.
        """
        # add plugin parameter to the db
        plugin_param = PluginParameter()
        plugin_param.plugin = plugin
        plugin_param.name = param['name']
        plg_type = param['type']
        plugin_param.type = [key for key in TYPES if TYPES[key]==plg_type][0]
        plugin_param.optional = param['optional']
        if param['default'] is None:
            plugin_param.default = ""
        else:
            plugin_param.default = str(param['default'])
        plugin_param.help = param['help']
        plugin_param.save()
        
    def add_plugin(self, dock_image_name):
        """
        Register/add a new plugin to the system.
        """
        # get representation from the corresponding app
        app_repr = self.get_plugin_app_representation(dock_image_name)
        name = self.get_plugin_name(app_repr)

        # check wether the plugin already exist
        existing_plugin_names = [plugin.name for plugin in Plugin.objects.all()]
        if name in existing_plugin_names:
            raise ValueError("Plugin '%s' already exists in the system" % name)

        # add plugin to the db
        plugin = Plugin()
        plugin.name = name
        plugin.dock_image = dock_image_name
        plugin.type = app_repr['type']
        plugin.authors = app_repr['authors']
        plugin.title = app_repr['title']
        plugin.category = app_repr['category']
        plugin.description = app_repr['description']
        plugin.documentation = app_repr['documentation']
        plugin.license = app_repr['license']
        plugin.version = app_repr['version']
        plugin.save()

        # add plugin's parameters to the db
        params = app_repr['parameters']
        for param in params:
            self._save_plugin_param(plugin, param)

    def get_plugin(self, name):
        """
        Get an existing/registered plugin.
        """
        try:
            plugin = Plugin.objects.get(name=name)
        except Plugin.DoesNotExist:
            raise NameError("Couldn't find '%s' plugin in the system" % name)
        return plugin
                  
    def remove_plugin(self, name):
        """
        Remove an existing/registered plugin from the system.
        """
        plugin = self.get_plugin(name)
        plugin.delete()

    def register_plugin_app_modification(self, dock_image_name):
        """
        Register/add new parameters to a plugin from the corresponding plugin's app.
        Also update plugin's fields and add the current date as a new plugin modification
        date.
        """
        # get representation from the corresponding app
        app_repr = self.get_plugin_app_representation(dock_image_name)
        name = self.get_plugin_name(app_repr)

        # update plugin fields (type cannot be changed as 'ds' plugins cannot have created
        # a feed in the DB)
        plugin = self.get_plugin(name)
        plugin.authors = app_repr['authors']
        plugin.title = app_repr['title']
        plugin.category = app_repr['category']
        plugin.description = app_repr['description']
        plugin.documentation = app_repr['documentation']
        plugin.license = app_repr['license']
        plugin.version = app_repr['version']

        # add there are new parameters then add them
        new_params = app_repr['parameters']
        existing_param_names = [parameter.name for parameter in plugin.parameters.all()]
        for param in new_params:
            if param['name'] not in existing_param_names:
                self._save_plugin_param(plugin, param)

        plugin.modification_date = timezone.now()
        plugin.save()

    def run(self, args=None):
        """
        Parse the arguments passed to the manager and perform the appropriate action.
        """
        options = self.parser.parse_args(args)
        if options.add:
            self.add_plugin(options.add)
        elif options.remove:
            self.remove_plugin(options.remove)
        elif options.modify:
            self.register_plugin_app_modification(options.modify)
        self.args = options



# ENTRYPOINT
if __name__ == "__main__":
    manager = PluginManager()
    manager.run()


