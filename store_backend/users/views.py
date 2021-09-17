
from django.contrib.auth.models import User

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.reverse import reverse

from collectionjson import services

from plugins.models import PluginMetaCollaborator
from plugins.serializers import PluginMetaSerializer, PluginMetaCollaboratorSerializer
from .serializers import UserSerializer
from .permissions import IsUser


class UserCreate(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json write template.
        """
        response = services.get_list_response(self, [])
        template_data = {"username": "", "password": "", "email": ""}
        return services.append_collection_template(response, template_data)


class UserDetail(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsUser,)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriden to append a collection+json template.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = Response(serializer.data)
        template_data = {"password": "", "email": ""}
        return services.append_collection_template(response, template_data)

    def update(self, request, *args, **kwargs):
        """
        Overriden to add required username before serializer validation.
        """
        user = self.get_object()
        request.data['username'] = user.username
        return super(UserDetail, self).update(request, *args, **kwargs)

    def perform_update(self, serializer):
        """
        Overriden to update user's password and email when requested by a PUT request.
        """
        serializer.save(email=serializer.validated_data.get("email"))
        user = self.get_object()
        password = serializer.validated_data.get("password")
        user.set_password(password)
        user.save()


class UserCollabPluginMetaList(generics.ListAPIView):
    """
    A view for the collection of user-specific plugin meta collaborators.
    """
    queryset = User.objects.all()
    serializer_class = PluginMetaCollaboratorSerializer
    permission_classes = (IsUser,)

    def list(self, request, *args, **kwargs):
        """
        Overriden to return the list of plugin meta collaborators for the queried user.
        """
        queryset = self.get_user_collab_plugin_metas_queryset()
        response = services.get_list_response(self, queryset)
        user = self.get_object()
        links = {'user': reverse('user-detail', request=request,
                                 kwargs={"pk": user.id})}
        return services.append_collection_links(response, links)

    def get_user_collab_plugin_metas_queryset(self):
        """
        Custom method to get the actual plugin meta collaborators queryset.
        """
        user = self.get_object()
        return PluginMetaCollaborator.objects.filter(user=user)


class UserFavoritePluginMetaList(generics.ListAPIView):
    """
    A view for the collection of user-specific plugin metas favored by the user.
    """
    queryset = User.objects.all()
    serializer_class = PluginMetaSerializer
    permission_classes = (IsUser,)

    def list(self, request, *args, **kwargs):
        """
        Overriden to return the list of favorite plugin metas for the queried user.
        """
        queryset = self.get_plugin_metas_queryset()
        response = services.get_list_response(self, queryset)
        user = self.get_object()
        links = {'user': reverse('user-detail', request=request,
                                 kwargs={"pk": user.id})}
        return services.append_collection_links(response, links)

    def get_plugin_metas_queryset(self):
        """
        Custom method to get the actual user-favorite plugin metas queryset.
        """
        user = self.get_object()
        return self.filter_queryset(user.favorite_plugin_metas.all())
