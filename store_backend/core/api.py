
from django.urls import path, include

from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.authtoken.views import obtain_auth_token

from plugins import views as plugin_views
from pipelines import views as pipeline_views
from users import views as user_views

# API v1 endpoints
urlpatterns = format_suffix_patterns([

    path('v1/auth-token/',
        obtain_auth_token),


    path('v1/users/',
        user_views.UserCreate.as_view(), name='user-create'),

    path('v1/users/<int:pk>/',
        user_views.UserDetail.as_view(), name='user-detail'),

    path('v1/users/<int:pk>/favoritepluginmetas/',
         user_views.UserFavoritePluginMetaList.as_view(),
         name='user-favoritepluginmeta-list'),

    path('v1/users/<int:pk>/collabpluginmetas/',
         user_views.UserCollabPluginMetaList.as_view(),
         name='user-pluginmetacollaborator-list'),


    path('v1/',
         plugin_views.PluginMetaList.as_view(),
         name='pluginmeta-list'),

    path('v1/search/',
         plugin_views.PluginMetaListQuerySearch.as_view(),
         name='pluginmeta-list-query-search'),

    path('v1/<int:pk>/',
         plugin_views.PluginMetaDetail.as_view(),
         name='pluginmeta-detail'),

    path('v1/<int:pk>/plugins/',
         plugin_views.PluginMetaPluginList.as_view(),
         name='pluginmeta-plugin-list'),

    path('v1/<int:pk>/collaborators/',
         plugin_views.PluginMetaCollaboratorList.as_view(),
         name='pluginmeta-pluginmetacollaborator-list'),


    path('v1/collaborators/<int:pk>/',
         plugin_views.PluginMetaCollaboratorDetail.as_view(),
         name='pluginmetacollaborator-detail'),


    path('v1/pluginstars/',
         plugin_views.PluginMetaStarList.as_view(), name='pluginmetastar-list'),

    path('v1/pluginstars/search/',
         plugin_views.PluginMetaStarListQuerySearch.as_view(),
         name='pluginmetastar-list-query-search'),

    path('v1/pluginstars/<int:pk>/',
         plugin_views.PluginMetaStarDetail.as_view(),
         name='pluginmetastar-detail'),


    path('v1/plugins/',
         plugin_views.PluginList.as_view(), name='plugin-list'),

    path('v1/plugins/search/',
         plugin_views.PluginListQuerySearch.as_view(), name='plugin-list-query-search'),

    path('v1/plugins/<int:pk>/',
        plugin_views.PluginDetail.as_view(), name='plugin-detail'),

    path('v1/plugins/<int:pk>/parameters/',
        plugin_views.PluginParameterList.as_view(), name='pluginparameter-list'),

    path('v1/plugins/parameters/<int:pk>/',
        plugin_views.PluginParameterDetail.as_view(), name='pluginparameter-detail'),


    path('v1/pipelines/',
        pipeline_views.PipelineList.as_view(),
        name='pipeline-list'),

    path('v1/pipelines/search/',
        pipeline_views.PipelineListQuerySearch.as_view(),
        name='pipeline-list-query-search'),

    path('v1/pipelines/<int:pk>/',
        pipeline_views.PipelineDetail.as_view(),
        name='pipeline-detail'),

    path('v1/pipelines/<int:pk>/plugins/',
        pipeline_views.PipelinePluginList.as_view(), name='pipeline-plugin-list'),

    path('v1/pipelines/<int:pk>/pipings/',
        pipeline_views.PipelinePluginPipingList.as_view(),
        name='pipeline-pluginpiping-list'),

    path('v1/pipelines/<int:pk>/parameters/',
        pipeline_views.PipelineDefaultParameterList.as_view(),
        name='pipeline-defaultparameter-list'),

    path('v1/pipelines/pipings/<int:pk>/',
        pipeline_views.PluginPipingDetail.as_view(),
        name='pluginpiping-detail'),

    path('v1/pipelines/string-parameter/<int:pk>/',
        pipeline_views.DefaultPipingStrParameterDetail.as_view(),
        name='defaultpipingstrparameter-detail'),

    path('v1/pipelines/integer-parameter/<int:pk>/',
        pipeline_views.DefaultPipingIntParameterDetail.as_view(),
        name='defaultpipingintparameter-detail'),

    path('v1/pipelines/float-parameter/<int:pk>/',
        pipeline_views.DefaultPipingFloatParameterDetail.as_view(),
        name='defaultpipingfloatparameter-detail'),

    path('v1/pipelines/boolean-parameter/<int:pk>/',
        pipeline_views.DefaultPipingBoolParameterDetail.as_view(),
        name='defaultpipingboolparameter-detail'),

])

# Login and logout views for Djangos' browsable API
urlpatterns += [
    path('v1/auth/', include('rest_framework.urls',  namespace='rest_framework')),
]
