
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class UserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(min_length=4, max_length=32,
                                     validators=[UniqueValidator(
                                         queryset=User.objects.all())])
    email = serializers.EmailField(required=True,
                                   validators=[UniqueValidator(
                                       queryset=User.objects.all())])
    password = serializers.CharField(min_length=8, max_length=100, write_only=True)
    favorite_plugin_metas = serializers.HyperlinkedIdentityField(
        view_name='user-favoritepluginmeta-list')
    owned_plugin_metas = serializers.HyperlinkedIdentityField(
        view_name='user-ownedpluginmeta-list')

    def create(self, validated_data):
        """
        Overriden to take care of the password hashing.
        """
        username = validated_data.get('username')
        email = validated_data.get('email')
        password = validated_data.get('password')
        return User.objects.create_user(username, email, password)

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email', 'password', 'favorite_plugin_metas',
                  'owned_plugin_metas')
