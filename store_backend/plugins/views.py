
from rest_framework import generics, permissions
from rest_framework.reverse import reverse

from collectionjson import services

from .models import Plugin, PluginFilter, PluginParameter
from .serializers import PluginSerializer,  PluginParameterSerializer
from .permissions import IsOwnerOrChrisOrReadOnly


class PluginList(generics.ListCreateAPIView):
    """
    A view for the collection of plugins.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        """
        Overriden to associate an owner with the plugin.
        """
        serializer.save(owner=[self.request.user])

    def create(self, request, *args, **kwargs):
        """
        Overriden to include required version descriptor in the request dict before
        serializer validation.
        """
        # we can assign any string here, this is required because of the
        # name,version unique together constraint in the model
        request.data['version'] = 'nullnull'
        return super(PluginList, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations, query list and a
        collection+json template to the response.
        """
        response = super(PluginList, self).list(request, *args, **kwargs)
        # append document-level link relations
        links = {'pipelines': reverse('pipeline-list', request=request)}
        user = self.request.user
        if user.is_authenticated:
            links['user'] = reverse('user-detail', request=request,
                                    kwargs={"pk": user.id})
        response = services.append_collection_links(response, links)
        # append query list
        query_list = [reverse('plugin-list-query-search', request=request)]
        response = services.append_collection_querylist(response, query_list)
        # append write template
        template_data = {'name': '', 'dock_image': '', 'public_repo': '',
                         'descriptor_file': ''}
        #import pdb; pdb.set_trace()
        return services.append_collection_template(response, template_data)


class PluginListQuerySearch(generics.ListAPIView):
    """
    A view for the collection of plugins resulting from a query search.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    filterset_class = PluginFilter
        

class PluginDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    A plugin view.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (IsOwnerOrChrisOrReadOnly,)

    def perform_update(self, serializer):
        """
        Overriden to update plugin's owners if requested by a PUT request.
        """
        if 'owner' in self.request.data:
            new_owner_username = self.request.data.pop('owner')
            new_owner = serializer.validate_new_owner(new_owner_username)
            plugin = self.get_object()
            plugin.add_owner(new_owner)
        super(PluginDetail, self).perform_update(serializer)

    def update(self, request, *args, **kwargs):
        """
        Overriden to override descriptors that are not allowed to be updated before
        serializer validation.
        """
        plugin = self.get_object()
        request.data['name'] = plugin.name
        request.data['dock_image'] = plugin.dock_image
        request.data['descriptor_file'] = plugin.descriptor_file
        request.data['version'] = plugin.version
        return super(PluginDetail, self).update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginDetail, self).retrieve(request, *args, **kwargs)
        template_data = {'public_repo': '', 'owner': ''}
        return services.append_collection_template(response, template_data)


class PluginParameterList(generics.ListAPIView):
    """
    A view for the collection of plugin parameters.
    """
    queryset = Plugin.objects.all()
    serializer_class = PluginParameterSerializer

    def list(self, request, *args, **kwargs):
        """
        Overriden to return the list of parameters for the queried plugin.
        """
        queryset = self.get_plugin_parameters_queryset()
        return services.get_list_response(self, queryset)

    def get_plugin_parameters_queryset(self):
        """
        Custom method to get the actual plugin parameters' queryset.
        """
        plugin = self.get_object()
        return self.filter_queryset(plugin.parameters.all())

    
class PluginParameterDetail(generics.RetrieveAPIView):
    """
    A plugin parameter view.
    """
    queryset = PluginParameter.objects.all()
    serializer_class = PluginParameterSerializer
