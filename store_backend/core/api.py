from django.conf.urls import url, include

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import obtain_auth_token

from plugins import views as plugin_views
from pipelines import views as pipeline_views
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

    url(r'^v1/search/$',
        plugin_views.PluginListQuerySearch.as_view(), name='plugin-list-query-search'),

    url(r'^v1/(?P<pk>[0-9]+)/$',
        plugin_views.PluginDetail.as_view(), name='plugin-detail'),

    url(r'^v1/(?P<pk>[0-9]+)/parameters/$',
        plugin_views.PluginParameterList.as_view(), name='pluginparameter-list'),

    url(r'^v1/parameters/(?P<pk>[0-9]+)/$',
        plugin_views.PluginParameterDetail.as_view(), name='pluginparameter-detail'),


    url(r'^v1/pipelines/$',
        pipeline_views.PipelineList.as_view(),
        name='pipeline-list'),

    url(r'^v1/pipelines/search/$',
        pipeline_views.PipelineListQuerySearch.as_view(),
        name='pipeline-list-query-search'),

    url(r'^v1/pipelines/(?P<pk>[0-9]+)/$',
        pipeline_views.PipelineDetail.as_view(),
        name='pipeline-detail'),

    url(r'^v1/pipelines/(?P<pk>[0-9]+)/plugins/$',
        pipeline_views.PipelinePluginList.as_view(), name='pipeline-plugin-list'),

    url(r'^v1/pipelines/(?P<pk>[0-9]+)/pipings/$',
        pipeline_views.PipelinePluginPipingList.as_view(),
        name='pipeline-pluginpiping-list'),

    url(r'^v1/pipelines/(?P<pk>[0-9]+)/parameters/$',
        pipeline_views.PipelineDefaultParameterList.as_view(),
        name='pipeline-defaultparameter-list'),

    url(r'^v1/pipelines/pipings/(?P<pk>[0-9]+)/$',
        pipeline_views.PluginPipingDetail.as_view(),
        name='pluginpiping-detail'),

    url(r'^v1/pipelines/string-parameter/(?P<pk>[0-9]+)/$',
        pipeline_views.DefaultPipingStrParameterDetail.as_view(),
        name='defaultpipingstrparameter-detail'),

    url(r'^v1/pipelines/integer-parameter/(?P<pk>[0-9]+)/$',
        pipeline_views.DefaultPipingIntParameterDetail.as_view(),
        name='defaultpipingintparameter-detail'),

    url(r'^v1/pipelines/float-parameter/(?P<pk>[0-9]+)/$',
        pipeline_views.DefaultPipingFloatParameterDetail.as_view(),
        name='defaultpipingfloatparameter-detail'),

    url(r'^v1/pipelines/boolean-parameter/(?P<pk>[0-9]+)/$',
        pipeline_views.DefaultPipingBoolParameterDetail.as_view(),
        name='defaultpipingboolparameter-detail'),

    url(r'^v1/pipelines/path-parameter/(?P<pk>[0-9]+)/$',
        pipeline_views.DefaultPipingPathParameterDetail.as_view(),
        name='defaultpipingpathparameter-detail'),

])

# Login and logout views for Djangos' browsable API
urlpatterns += [
    url(r'^v1/auth/', include('rest_framework.urls',  namespace='rest_framework')),
]
