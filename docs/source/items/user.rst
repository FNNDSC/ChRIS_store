=========
User item
=========

.. _Collection+JSON: http://amundsen.com/media-types/collection/

.. _`link relation`: http://amundsen.com/media-types/collection/format/#link-relations


**Read/write**


This resource type refers to a registered store user.

In other Collection+JSON_ resource representations this resource type is linked by any
`link relation`_ with attribute:

``"rel": "owner"`` or ``"rel": "user"``


.. http:get:: /api/v1/users/(int:user_id)/

   :synopsis: Gets a registered user.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/users/2/ HTTP/1.1
      Host: localhost:8010
      Accept: application/vnd.collection+json


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Allow: GET
      Content-Type: application/vnd.collection+json

        {
            "collection": {
                "href": "http://localhost:8010/api/v1/users/2/",
                "items": [
                    {
                        "data": [
                            {
                                "name": "username",
                                "value": "cube"
                            },
                            {
                                "name": "email",
                                "value": "cube@babymri.org"
                            }
                        ],
                        "href": "http://localhost:8010/api/v1/users/2/",
                        "links": [
                            {
                                "href": "http://localhost:8010/api/v1/1/",
                                "rel": "plugin"
                            },
                            {
                                "href": "http://localhost:8010/api/v1/2/",
                                "rel": "plugin"
                            }
                        ]
                    }
                ],
                "links": [],
                "template": {
                    "data": [
                        {
                            "name": "email",
                            "value": ""
                        },
                        {
                            "name": "password",
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
   :statuscode 404: not found

   .. |--| unicode:: U+2013   .. en dash

   .. _Properties: http://amundsen.com/media-types/collection/format/#properties
   .. _`Link Relations`: http://amundsen.com/media-types/collection/format/#link-relations

   Properties_ (API semantic descriptors):

    - **username** (`string`) |--| user's username
    - **email** (`string`) |--| user's email

   `Link Relations`_:

    - **plugin** |--| links to a user's owned plugin_

   .. _plugin: plugin.html
