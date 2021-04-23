
from rest_framework import generics, permissions
from rest_framework.reverse import reverse

from collectionjson import services

from .models import (PluginMeta, PluginMetaFilter, PluginMetaStar, PluginMetaStarFilter,
                     Plugin, PluginFilter, PluginParameter)
from .serializers import (PluginMetaSerializer, PluginMetaStarSerializer,
                          PluginSerializer, PluginParameterSerializer)
from .permissions import (IsOwnerOrChrisOrReadOnly, IsMetaOwnerOrChrisOrReadOnly,
                          IsStarOwnerOrChris)


class PluginMetaList(generics.ListAPIView):
    """
    A view for the collection of plugin metas.
    """
    queryset = PluginMeta.objects.all()
    serializer_class = PluginMetaSerializer

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations and a query list to the
        response.
        """
        response = super(PluginMetaList, self).list(request, *args, **kwargs)
        # append document-level link relations
        links = {'plugin_stars': reverse('pluginmetastar-list', request=request),
                 'plugins': reverse('plugin-list', request=request),
                 'pipelines': reverse('pipeline-list', request=request)}
        user = self.request.user
        if user.is_authenticated:
            links.update({
                'user': reverse('user-detail', request=request, kwargs={"pk": user.id}),
                'favorite_plugin_metas': reverse('user-favoritepluginmeta-list',
                                                 request=request, kwargs={"pk": user.id}),
                'owned_plugin_metas': reverse('user-ownedpluginmeta-list',
                                              request=request, kwargs={"pk": user.id})
            })
        response = services.append_collection_links(response, links)
        # append query list
        query_list = [reverse('pluginmeta-list-query-search', request=request)]
        return services.append_collection_querylist(response, query_list)


class PluginMetaListQuerySearch(generics.ListAPIView):
    """
    A view for the collection of plugin metas resulting from a query search.
    """
    serializer_class = PluginMetaSerializer
    queryset = PluginMeta.objects.all()
    filterset_class = PluginMetaFilter


class PluginMetaDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    A plugin meta view.
    """
    serializer_class = PluginMetaSerializer
    queryset = PluginMeta.objects.all()
    permission_classes = (IsOwnerOrChrisOrReadOnly,)

    def perform_update(self, serializer):
        """
        Overriden to update plugin's owners if requested by a PUT request.
        """
        meta = self.get_object()
        
        super(PluginMetaDetail, self).perform_update(serializer)

    def update(self, request, *args, **kwargs):
        """
        Overriden to remove descriptors that are not allowed to be updated before
        the serializer performs validation.
        """
        plugin_meta = self.get_object()
         # name is required
        # these are part o
       
        
               
        return super(PluginMetaDetail, self).update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginMetaDetail, self).retrieve(request, *args,
                                                                     **kwargs)
        template_data = {'public_repo': '', 'new_owner': ''}
        return services.append_collection_template(response, template_data)


class PluginMetaPluginList(generics.ListAPIView):
    """
    A view for the collection of meta-specific plugins.
    """
    queryset = PluginMeta.objects.all()
    serializer_class = PluginSerializer

    def list(self, request, *args, **kwargs):
        """
        Overriden to return a list of the plugins for the queried  meta.
        """
        queryset = self.get_plugins_queryset()
        response = services.get_list_response(self, queryset)
        meta = self.get_object()
        links = {'meta': reverse('pluginmeta-detail', request=request,
                                 kwargs={"pk": meta.id})}
        return services.append_collection_links(response, links)

    def get_plugins_queryset(self):
        """
        Custom method to get the actual plugins queryset.
        """
        meta = self.get_object()
        return self.filter_queryset(meta.plugins.all())


class PluginMetaStarList(generics.ListCreateAPIView):
    """
    A view for the collection of plugins' stars.
    """
    serializer_class = PluginMetaStarSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Overriden to return a custom queryset that is only comprised by the plugin
        meta stars created by the currently authenticated user.
        """
        user = self.request.user
        # if the user is chris then return all the plugin meta stars in the system
        if user.username == 'chris':
            return PluginMetaStar.objects.all()
        return PluginMetaStar.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Overriden to associate a plugin and authenticated user with the plugin star.
        """
        user = self.request.user
        plugin_meta = serializer.validated_data.get('meta').get('name')
        serializer.save(meta=plugin_meta, user=user)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations, query list and a
        collection+json template to the response.
        """
        response = super(PluginMetaStarList, self).list(request, *args, **kwargs)
        # append document-level link relations
        links = {'plugins': reverse('plugin-list', request=request)}
        user = self.request.user
        if user.is_authenticated:
            links['user'] = reverse('user-detail', request=request,
                                    kwargs={"pk": user.id})
        response = services.append_collection_links(response, links)
        # append query list
        query_list = [reverse('pluginmetastar-list-query-search', request=request)]
        response = services.append_collection_querylist(response, query_list)
        # append write template
        template_data = {'plugin_name': ''}
        return services.append_collection_template(response, template_data)


class PluginMetaStarListQuerySearch(generics.ListAPIView):
    """
    A view for the collection of plugin stars resulting from a query search.
    """
    serializer_class = PluginMetaStarSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = PluginMetaStarFilter

    def get_queryset(self):
        """
        Overriden to return a custom queryset that is only comprised by the plugin
        meta stars created by the currently authenticated user.
        """
        user = self.request.user
        # if the user is chris then return all the plugin meta stars in the system
        if user.username == 'chris':
            return PluginMetaStar.objects.all()
        return PluginMetaStar.objects.filter(user=user)


class PluginMetaStarDetail(generics.RetrieveDestroyAPIView):
    """
    A plugin star view.
    """
    queryset = PluginMetaStar.objects.all()
    serializer_class = PluginMetaStarSerializer
    permission_classes = (IsStarOwnerOrChris,)


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
        # we can use any random version string that is not likely to be already in the DB
        # for this plugin's name, this is required because of the name,version unique
        # together constraint in the model
        request.data['version'] = 'random_str'
        return super(PluginList, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations, query list and a
        collection+json template to the response.
        """
        response = super(PluginList, self).list(request, *args, **kwargs)
        # append document-level link relations
        links = {'plugin_stars': reverse('pluginmetastar-list', request=request),
                 'pipelines': reverse('pipeline-list', request=request)}
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
        return services.append_collection_template(response, template_data)


class PluginListQuerySearch(generics.ListAPIView):
    """
    A view for the collection of plugins resulting from a query search.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    filterset_class = PluginFilter


class PluginDetail(generics.RetrieveDestroyAPIView):
    """
    A plugin view.
    """
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (IsMetaOwnerOrChrisOrReadOnly,)

    def perform_destroy(self, instance):
        """
        Overriden to delete the associated plugin meta if this is the last plugin.
        """
        if instance.meta.plugins.count() == 1:
            instance.meta.delete()  # the cascade deletes the plugin too
        else:
            instance.delete()


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
