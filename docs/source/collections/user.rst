===============
User collection
===============

.. _Collection+JSON: http://amundsen.com/media-types/collection/

.. _user: ../items/user.html


**Write-only**


This resource type refers to the collection of registered users.


.. http:post:: /api/v1/users/

   :synopsis: Creates a new user account.

   **Example request**:

   .. sourcecode:: http

      POST /api/v1/users/ HTTP/1.1
      Host: localhost:8010
      Accept: application/vnd.collection+json


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Allow: POST
      Content-Type: application/vnd.collection+json

        {
            "collection": {
                "href": "http://localhost:8010/api/v1/users/",
                "items": [
                    {
                        "data": [
                            {
                                "name": "username",
                                "value": "bob"
                            },
                            {
                                "name": "email",
                                "value": "bob@babymri.org"
                            }
                        ],
                        "href": "http://localhost:8010/api/v1/users/6/"
                    }
                ],
                "links": [],
                "version": "1.0"
            }
        }


   :reqheader Accept: application/vnd.collection+json
   :resheader Content-Type: application/vnd.collection+json
   :statuscode 201: Created

   .. |--| unicode:: U+2013   .. en dash

   .. _Properties: http://amundsen.com/media-types/collection/format/#properties

   Properties_ (API semantic descriptors):

    - user_ item properties

