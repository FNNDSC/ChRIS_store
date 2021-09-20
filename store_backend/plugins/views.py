
from rest_framework import generics, permissions
from rest_framework.reverse import reverse

from collectionjson import services

from .models import (PluginMeta, PluginMetaFilter, PluginMetaStar, PluginMetaStarFilter,
                     Plugin, PluginFilter, PluginParameter, PluginMetaCollaborator)
from .serializers import (PluginMetaSerializer, PluginMetaStarSerializer,
                          PluginMetaCollaboratorSerializer,
                          PluginSerializer, PluginParameterSerializer)
from .permissions import (IsStarOwnerOrReadOnly, IsMetaOwnerOrReadOnly,
                          IsObjMetaOwnerOrReadOnly, IsObjMetaOwnerAndNotUserOrReadOnly)


class PluginMetaList(generics.ListAPIView):
    """
    A view for the collection of plugin metas.
    """
    http_method_names = ['get']
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
                'collab_plugin_metas': reverse('user-pluginmetacollaborator-list',
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
    http_method_names = ['get']
    serializer_class = PluginMetaSerializer
    queryset = PluginMeta.objects.all()
    filterset_class = PluginMetaFilter


class PluginMetaDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    A plugin meta view.
    """
    http_method_names = ['get', 'put', 'delete']
    serializer_class = PluginMetaSerializer
    queryset = PluginMeta.objects.all()
    permission_classes = (IsMetaOwnerOrReadOnly,)

    def update(self, request, *args, **kwargs):
        """
        Overriden to remove descriptors that are not allowed to be updated before
        the serializer performs validation.
        """
        plugin_meta = self.get_object()
        request.data['name'] = plugin_meta.name  # name is required
        # these are part of the plugin repr. and are not allowed to be changed with PUT
        request.data.pop('title', None)
        request.data.pop('license', None)
        request.data.pop('type', None)
        request.data.pop('icon', None)
        request.data.pop('category', None)
        request.data.pop('authors', None)
        request.data.pop('documentation', None)
        return super(PluginMetaDetail, self).update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginMetaDetail, self).retrieve(request, *args, **kwargs)
        template_data = {'public_repo': ''}
        return services.append_collection_template(response, template_data)


class PluginMetaPluginList(generics.ListAPIView):
    """
    A view for the collection of meta-specific plugins.
    """
    http_method_names = ['get']
    queryset = PluginMeta.objects.all()
    serializer_class = PluginSerializer

    def list(self, request, *args, **kwargs):
        """
        Overriden to return a list of the plugins for the queried meta.
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
    A view for the collection of plugin metas' stars.
    """
    http_method_names = ['get', 'post']
    queryset = PluginMetaStar.objects.all()
    serializer_class = PluginMetaStarSerializer
    permission_classes = (permissions.IsAuthenticated,)

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
    http_method_names = ['get']
    serializer_class = PluginMetaStarSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = PluginMetaStarFilter


class PluginMetaStarDetail(generics.RetrieveDestroyAPIView):
    """
    A plugin star view.
    """
    http_method_names = ['get', 'delete']
    queryset = PluginMetaStar.objects.all()
    serializer_class = PluginMetaStarSerializer
    permission_classes = (permissions.IsAuthenticated, IsStarOwnerOrReadOnly,)


class PluginMetaCollaboratorList(generics.ListCreateAPIView):
    """
    A view for the collection of plugin meta-specific plugin meta collaborator list.
    """
    http_method_names = ['get', 'post']
    queryset = PluginMeta.objects.all()
    serializer_class = PluginMetaCollaboratorSerializer
    permission_classes = (permissions.IsAuthenticated, IsMetaOwnerOrReadOnly,)

    def get_plugin_meta_collaborators_queryset(self):
        """
        Custom method to get the actual plugin meta's plugin meta collaborators queryset.
        """
        plg_meta = self.get_object()
        return PluginMetaCollaborator.objects.filter(meta=plg_meta)

    def perform_create(self, serializer):
        """
        Overriden to associate a plugin meta with the plugin meta collaborator.
        """
        plg_meta = self.get_object()
        user = serializer.validated_data['user']['username']
        serializer.save(meta=plg_meta, user=user)

    def list(self, request, *args, **kwargs):
        """
        Overriden to append document-level link relations and a collection+json template
        to the response.
        """
        queryset = self.get_plugin_meta_collaborators_queryset()
        response = services.get_list_response(self, queryset)
        plg_meta = self.get_object()
        # append document-level link relations
        links = {'meta': reverse('pluginmeta-detail', request=request,
                                 kwargs={"pk": plg_meta.id})}
        response = services.append_collection_links(response, links)
        # append write template
        template_data = {'username': '', 'role': ''}
        return services.append_collection_template(response, template_data)


class PluginMetaCollaboratorDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    A plugin star view.
    """
    http_method_names = ['get', 'put', 'delete']
    queryset = PluginMetaCollaborator.objects.all()
    serializer_class = PluginMetaCollaboratorSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsObjMetaOwnerAndNotUserOrReadOnly,)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        response = super(PluginMetaCollaboratorDetail, self).retrieve(request, *args,
                                                                      **kwargs)
        template_data = {'role': ''}
        return services.append_collection_template(response, template_data)


class PluginList(generics.ListCreateAPIView):
    """
    A view for the collection of plugins.
    """
    http_method_names = ['get', 'post']
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        """
        Overriden to pass the request user to the serializer's create method.
        """
        serializer.save(user=self.request.user)

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
    http_method_names = ['get']
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    filterset_class = PluginFilter


class PluginDetail(generics.RetrieveDestroyAPIView):
    """
    A plugin view.
    """
    http_method_names = ['get', 'delete']
    serializer_class = PluginSerializer
    queryset = Plugin.objects.all()
    permission_classes = (IsObjMetaOwnerOrReadOnly,)

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
    http_method_names = ['get']
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
    http_method_names = ['get']
    queryset = PluginParameter.objects.all()
    serializer_class = PluginParameterSerializer
