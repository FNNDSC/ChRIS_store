===========
Plugin item
===========

.. _Collection+JSON: http://amundsen.com/media-types/collection/

.. _`link relation`: http://amundsen.com/media-types/collection/format/#link-relations


**Read/write**


This resource type refers to a plugin item.

In other Collection+JSON_ resource representations this resource type is linked by any
`link relation`_ with attribute:

``"rel": "plugin"``


..  http:get:: /api/v1/(int:plugin_id)/

    :synopsis: Gets a system plugin.

    **Example request**:

    .. sourcecode:: http

      GET /api/v1/1/ HTTP/1.1
      Host: localhost:8010
      Accept: application/vnd.collection+json


    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK
      Allow: GET
      Content-Type: application/vnd.collection+json

        {
            "collection": {
                "href": "http://localhost:8010/api/v1/1/",
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
                    }
                ],
                "links": [],
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
                        }
                    ]
                },
                "version": "1.0"
            }
        }



    :reqheader Accept: application/vnd.collection+json
    :resheader Content-Type: application/vnd.collection+json
    :statuscode 200: no error
    :statuscode 400: bad request
    :statuscode 401: authentication credentials were not provided
    :statuscode 404: not found

    .. |--| unicode:: U+2013   .. en dash

    .. _Properties: http://amundsen.com/media-types/collection/format/#properties
    .. _`Link Relations`: http://amundsen.com/media-types/collection/format/#link-relations

    Properties_ (API semantic descriptors):

    - **name** (`string`) |--| plugin's name
    - **dock_image** (`string`) |--| plugin's docker image name
    - **public_repo** (`string`) |--| plugin's public source code repo (must be a valid url)
    - **type** (`string`) |--| plugin's type. Can only be the strings 'fs' (filesystem
      plugin) or 'ds' (data plugin)

    `Link Relations`_:

    - **parameters** |--| links to the plugin's `collection of parameters`_
    - **owner** |--| links to the plugin's owner `user item`_

    .. _`collection of parameters`: ../collections/plugin_parameter.html
    .. _`user item`: ../user.html
