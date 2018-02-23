
from rest_framework import generics, permissions
from rest_framework.reverse import reverse

from collectionjson import services

from .models import Plugin, PluginFilter, PluginParameter
from .serializers import PluginSerializer,  PluginParameterSerializer
from .permissions import IsOwnerOrChrisOrReadOnly, IsRelatedPluginOwnerOrChrisOrReadOnly


class PluginList(generics.ListCreateAPIView):
    """
    A view for the collection of plugins.
    """
    serializer_class = PluginSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Overriden to return a custom queryset that is only comprised by the plugins
        owned by the currently authenticated user.
        """
        user = self.request.user
        # if the user is chris then return all the plugins in the system
        if (user.username == 'chris'):
            return Plugin.objects.all()
        return Plugin.objects.filter(owner=user)

    def perform_create(self, serializer):
        """
        Overriden to associate an owner with the plugin before first
        saving to the DB.
        """
        serializer.save(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations and a collection+json template
        to the response.
        """
        response = super(PluginList, self).list(request, *args, **kwargs)
        user = self.request.user
        links = {'all_plugins': reverse('full-plugin-list', request=request),
                 'user': reverse('user-detail', request=request, kwargs={"pk": user.id})}
        response = services.append_collection_links(response, links)
        template_data = {'name': '', 'dock_image': '', 'public_repo': '',
                         'descriptor_file': ''}
        return services.append_collection_template(response, template_data)


class FullPluginList(generics.ListAPIView):
    """
    A view for the full collection of plugins.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations.
        """
        response = super(FullPluginList, self).list(request, *args, **kwargs)
        links = {'plugins': reverse('plugin-list', request=request)}
        return services.append_collection_links(response, links)


class PluginListQuerySearch(generics.ListAPIView):
    """
    A view for the collection of plugins resulting from a query search.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    filter_class = PluginFilter
        

class PluginDetail(generics.RetrieveUpdateAPIView):
    """
    A plugin view.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrChrisOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginDetail, self).retrieve(request, *args, **kwargs)
        template_data = {'dock_image': '', 'public_repo': '', 'descriptor_file': ''}
        return services.append_collection_template(response, template_data)

    def update(self, request, *args, **kwargs):
        """
        Overriden to add required field before serializer validation.
        """
        plugin = self.get_object()
        request.data['name'] = plugin.name
        return super(PluginDetail, self).update(request, *args, **kwargs)


class PluginParameterList(generics.ListCreateAPIView):
    """
    A view for the collection of plugin parameters.
    """
    queryset = Plugin.objects.all()
    serializer_class = PluginParameterSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrChrisOrReadOnly,)

    def perform_create(self, serializer):
        """
        Overriden to associate a plugin with the plugin parameter before first
        saving to the DB.
        """
        plugin = self.get_object()
        serializer.save(plugin=plugin)

    def list(self, request, *args, **kwargs):
        """
        Overriden to return the list of parameters for the queried plugin.
        A collection+json template is also added to the response.
        """
        queryset = self.get_plugin_parameters_queryset()
        response = services.get_list_response(self, queryset)
        template_data = { 'name': '', 'type': '', 'optional': '', 'default': '',
                          'help': ''}
        return services.append_collection_template(response, template_data)

    def get_plugin_parameters_queryset(self):
        """
        Custom method to get the actual plugin parameters' queryset.
        """
        plugin = self.get_object()
        return self.filter_queryset(plugin.parameters.all())

    
class PluginParameterDetail(generics.RetrieveUpdateAPIView):
    """
    A plugin parameter view.
    """
    queryset = PluginParameter.objects.all()
    serializer_class = PluginParameterSerializer
    permission_classes = (permissions.IsAuthenticated, IsRelatedPluginOwnerOrChrisOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginParameterDetail, self).retrieve(request, *args, **kwargs)
        template_data = {'name': '', 'type': '', 'optional': '', 'default': '',
                         'help': ''}
        return services.append_collection_template(response, template_data)