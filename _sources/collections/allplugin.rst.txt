=====================
All plugin collection
=====================

.. _Collection+JSON: http://amundsen.com/media-types/collection/

.. _`link relation`: http://amundsen.com/media-types/collection/format/#link-relations

.. _plugin: ../items/plugin.html


**Read-only**


This resource type refers to the collection of all plugin_ items for all users of the store.

In other Collection+JSON_ resource representations this resource type is linked by any
`link relation`_ with attribute:

``"rel": "all_plugins"``


.. http:get:: /api/v1/plugins/

   :synopsis: Gets the list of all the plugins in the store.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/plugins/ HTTP/1.1
      Host: localhost:8010
      Accept: application/vnd.collection+json


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Allow: GET
      Content-Type: application/vnd.collection+json

        {
            "collection": {
                "href": "http://localhost:8010/api/v1/plugins/",
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
                        "href": "http://localhost:8010/api/v1/",
                        "rel": "plugins"
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
    - **plugins** |--| links to the user-specific `collection of plugins`_ for the
      currently authenticated user

   .. _`collection of plugins`: plugin.html
