from django.conf.urls import url, include

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import obtain_auth_token

from plugins import views as plugin_views
from users import views as user_views

# API v1 endpoints
urlpatterns = format_suffix_patterns([

    url(r'^v1/auth-token/$',
        obtain_auth_token),


    url(r'^v1/users/$',
        user_views.UserCreate.as_view(), name='user-create'),

    url(r'^v1/users/(?P<pk>[0-9]+)/$',
        user_views.UserDetail.as_view(), name='user-detail'),


    url(r'^v1/$',
        plugin_views.PluginList.as_view(), name='plugin-list'),

    url(r'^v1/user-plugins/$',
        plugin_views.UserPluginList.as_view(), name='user-plugin-list'),

    url(r'^v1/search/$',
        plugin_views.PluginListQuerySearch.as_view(), name='plugin-list-query-search'),

    url(r'^v1/(?P<pk>[0-9]+)/$',
        plugin_views.PluginDetail.as_view(), name='plugin-detail'),

    url(r'^v1/(?P<pk>[0-9]+)/parameters/$',
        plugin_views.PluginParameterList.as_view(), name='pluginparameter-list'),

    url(r'^v1/parameters/(?P<pk>[0-9]+)/$',
        plugin_views.PluginParameterDetail.as_view(), name='pluginparameter-detail'),

])

# Login and logout views for Djangos' browsable API
urlpatterns += [
    url(r'^v1/auth/', include('rest_framework.urls',  namespace='rest_framework')),
]