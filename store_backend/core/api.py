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

    url(r'^v1/user/$',
        user_views.UserList.as_view(), name='user-list'),


    url(r'^v1/plugins/$',
        plugin_views.PluginList.as_view(), name='plugin-list'),

    url(r'^v1/plugins/search/$',
        plugin_views.PluginListQuerySearch.as_view(), name='plugin-list-query-search'),

    url(r'^v1/plugins/(?P<pk>[0-9]+)/$',
        plugin_views.PluginDetail.as_view(), name='plugin-detail'),

    url(r'^v1/plugins/(?P<pk>[0-9]+)/parameters/$',
        plugin_views.PluginParameterList.as_view(), name='pluginparameter-list'),

    url(r'^v1/plugins/parameters/(?P<pk>[0-9]+)/$',
        plugin_views.PluginParameterDetail.as_view(), name='pluginparameter-detail'),

    url(r'^v1/plugins/string-parameter/(?P<pk>[0-9]+)/$',
        plugin_views.StringParameterDetail.as_view(), name='stringparameter-detail'),

    url(r'^v1/plugins/int-parameter/(?P<pk>[0-9]+)/$',
        plugin_views.IntParameterDetail.as_view(), name='intparameter-detail'),

    url(r'^v1/plugins/float-parameter/(?P<pk>[0-9]+)/$',
        plugin_views.FloatParameterDetail.as_view(), name='floatparameter-detail'),

    url(r'^v1/plugins/bool-parameter/(?P<pk>[0-9]+)/$',
        plugin_views.BoolParameterDetail.as_view(), name='boolparameter-detail'),

    url(r'^v1/plugins/path-parameter/(?P<pk>[0-9]+)/$',
        plugin_views.PathParameterDetail.as_view(), name='pathparameter-detail'),

])

# Login and logout views for Djangos' browsable API
urlpatterns += [
    url(r'^v1/auth/', include('rest_framework.urls',  namespace='rest_framework')),
]