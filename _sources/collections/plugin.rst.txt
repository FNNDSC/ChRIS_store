=================
Plugin collection
=================

.. _Collection+JSON: http://amundsen.com/media-types/collection/

.. _`link relation`: http://amundsen.com/media-types/collection/format/#link-relations

.. _plugin: ../items/plugin.html


**Read/write**


This resource type refers a collection of user-specific plugin_ items.

In other Collection+JSON_ resource representations this resource type is linked by any
`link relation`_ with attribute:

``"rel": "plugins"``


.. http:get:: /api/v1/plugins/

   :synopsis: Gets the list of plugins owned by the authenticated user.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/ HTTP/1.1
      Host: localhost:8010
      Accept: application/vnd.collection+json


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Allow: GET
      Content-Type: application/vnd.collection+json

        {
            "collection": {
                "href": "http://localhost:8010/api/v1/",
                "items": [
                    {
                        "data": [
                            {
                                "name": "name",
                                "value": "simplefsapp"
                            },
                            {
                                "name": "creation_date",
                                "value": "2018-03-20T16:43:20.869836Z"
                            },
                            {
                                "name": "modification_date",
                                "value": "2018-03-20T16:43:20.869885Z"
                            },
                            {
                                "name": "dock_image",
                                "value": "fnndsc/pl-simplefsapp"
                            },
                            {
                                "name": "public_repo",
                                "value": "https://github.com/FNNDSC/pl-simplefsapp"
                            },
                            {
                                "name": "type",
                                "value": "fs"
                            },
                            {
                                "name": "authors",
                                "value": "FNNDSC (dev@babyMRI.org)"
                            },
                            {
                                "name": "title",
                                "value": "Simple chris fs app"
                            },
                            {
                                "name": "category",
                                "value": ""
                            },
                            {
                                "name": "description",
                                "value": "A simple chris fs app demo"
                            },
                            {
                                "name": "documentation",
                                "value": "http://wiki"
                            },
                            {
                                "name": "license",
                                "value": "Opensource (MIT)"
                            },
                            {
                                "name": "version",
                                "value": "0.1"
                            },
                            {
                                "name": "execshell",
                                "value": "python3"
                            },
                            {
                                "name": "selfpath",
                                "value": "/usr/src/simplefsapp"
                            },
                            {
                                "name": "selfexec",
                                "value": "simplefsapp.py"
                            }
                        ],
                        "href": "http://localhost:8010/api/v1/1/",
                        "links": [
                            {
                                "href": "http://localhost:8010/api/v1/1/parameters/",
                                "rel": "parameters"
                            },
                            {
                                "href": "http://localhost:8010/api/v1/users/2/",
                                "rel": "owner"
                            }
                        ]
                    },
                    {
                        "data": [
                            {
                                "name": "name",
                                "value": "simpledsapp"
                            },
                            {
                                "name": "creation_date",
                                "value": "2018-03-20T16:43:55.705545Z"
                            },
                            {
                                "name": "modification_date",
                                "value": "2018-03-20T16:43:55.705603Z"
                            },
                            {
                                "name": "dock_image",
                                "value": "fnndsc/pl-simpledsapp"
                            },
                            {
                                "name": "public_repo",
                                "value": "https://github.com/FNNDSC/pl-simpledsapp"
                            },
                            {
                                "name": "type",
                                "value": "ds"
                            },
                            {
                                "name": "authors",
                                "value": "FNNDSC (dev@babyMRI.org)"
                            },
                            {
                                "name": "title",
                                "value": "Simple chris ds app"
                            },
                            {
                                "name": "category",
                                "value": ""
                            },
                            {
                                "name": "description",
                                "value": "A simple chris ds app demo"
                            },
                            {
                                "name": "documentation",
                                "value": "http://wiki"
                            },
                            {
                                "name": "license",
                                "value": "Opensource (MIT)"
                            },
                            {
                                "name": "version",
                                "value": "0.1"
                            },
                            {
                                "name": "execshell",
                                "value": "python3"
                            },
                            {
                                "name": "selfpath",
                                "value": "/usr/src/simpledsapp"
                            },
                            {
                                "name": "selfexec",
                                "value": "simpledsapp.py"
                            }
                        ],
                        "href": "http://localhost:8010/api/v1/2/",
                        "links": [
                            {
                                "href": "http://localhost:8010/api/v1/2/parameters/",
                                "rel": "parameters"
                            },
                            {
                                "href": "http://localhost:8010/api/v1/users/2/",
                                "rel": "owner"
                            }
                        ]
                    }
                ],
                "links": [
                    {
                        "href": "http://localhost:8010/api/v1/users/2/",
                        "rel": "user"
                    },
                    {
                        "href": "http://localhost:8010/api/v1/plugins/",
                        "rel": "all_plugins"
                    }
                ],
                "queries": [
                    {
                        "data": [
                            {
                                "name": "name",
                                "value": ""
                            },
                            {
                                "name": "dock_image",
                                "value": ""
                            },
                            {
                                "name": "public_repo",
                                "value": ""
                            },
                            {
                                "name": "type",
                                "value": ""
                            },
                            {
                                "name": "category",
                                "value": ""
                            },
                            {
                                "name": "owner_username",
                                "value": ""
                            },
                            {
                                "name": "min_creation_date",
                                "value": ""
                            },
                            {
                                "name": "max_creation_date",
                                "value": ""
                            }
                        ],
                        "href": "http://localhost:8010/api/v1/search/",
                        "rel": "search"
                    }
                ],
                "template": {
                    "data": [
                        {
                            "name": "dock_image",
                            "value": ""
                        },
                        {
                            "name": "public_repo",
                            "value": ""
                        },
                        {
                            "name": "descriptor_file",
                            "value": ""
                        },
                        {
                            "name": "name",
                            "value": ""
                        }
                    ]
                },
                "version": "1.0"
            }
        }


   :reqheader Accept: application/vnd.collection+json
   :resheader Content-Type: application/vnd.collection+json
   :statuscode 200: no error
   :statuscode 401: authentication credentials were not provided

   .. |--| unicode:: U+2013   .. en dash

   .. _Properties: http://amundsen.com/media-types/collection/format/#properties
   .. _`Link Relations`: http://amundsen.com/media-types/collection/format/#link-relations

   Properties_ (API semantic descriptors):

    - plugin_ item properties

   `Link Relations`_:

    - plugin_ item link relations
    - **all_plugins** |--| links to the `collection of all plugins`_ for the currently authenticated
    - **user** |--| links to the currently authenticated `user item`_

   .. _`collection of all plugins`: allplugin.html
   .. _`user item`: ../items/user.html