==================
REST API Reference
==================

This API uses the standard Collection+JSON_ hypermedia type to exchange resource
representations with clients. All the functionality provided by the API can be
discovered by clients by doing :http:method:`get` requests to links ("href" elements)
presented by the hypermedia documents returned by the web server, starting with the API's
"home page".

.. _Collection+JSON: http://amundsen.com/media-types/collection/


The API's "home page" relative url is: /api/v1/ which serves a user-specific `collection
of plugins`_.

.. _`collection of plugins`: collections/plugin.html


There are two main types of resources served by the API:

**Collection**
  A resource to group other resources together. Its representation focuses on links to
  other resources, though it may also include snippets from the representations of those
  other resources.

**Item**
  A standalone resource that is linked to from a collection’s representation.


The following table shows the API's HTTP protocol semantics for these resource types:


.. table:: **API's accepted HTTP requests**

	=====================  =====================  =====================    =====================  =====================
                           Collection resource                                            Item resource
	-------------------------------------------------------------------    --------------------------------------------
	read-only              read/write             write-only               read-only              read/write
	=====================  =====================  =====================    =====================  =====================
	:http:method:`get`     :http:method:`get`     :http:method:`post`      :http:method:`get`     :http:method:`get`

	                       :http:method:`post`                                                    :http:method:`put`
	=====================  =====================  =====================    =====================  =====================




Following are the actuall lists of resource types:


**Collections:**

.. toctree::
   :maxdepth: 2

   collections/plugin
   collections/allplugin
   collections/plugin_parameter
   collections/user


**Items:**

.. toctree::
   :maxdepth: 2

   items/plugin
   items/plugin_parameter
   items/user
