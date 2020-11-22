Installation
============================================


Currently the only way to install django-imagedeck is through the repository:

.. code-block:: bash

    pip install git+https://gitlab.unimelb.edu.au/rturnbull/django-imagedeck.git

Then add the necessary apps to your ``INSTALLED_APPS`` in your settings:

.. code-block:: python
   :emphasize-lines: 3-5

    INSTALLED_APPS = [
        ...
        "filer",
        "adminsortable2",
        "imagedeck",
        ...
    ]


Configuration
--------------

The following values are set be default and you can override them in your Django settings:

.. code-block:: python

    IMAGEDECK_THUMBNAIL_WIDTH = 250
    IMAGEDECK_THUMBNAIL_HEIGHT = None
    IMAGEDECK_THUMBNAIL_QUALITY = 60
    IMAGEDECK_THUMBNAIL_FORMAT = "JPEG"
    IMAGEDECK_DEFAULT_WIDTH = 250
    IMAGEDECK_DEFAULT_HEIGHT = 250


If ``IMAGEDECK_THUMBNAIL_HEIGHT`` is None, then it uses the aspect ratio of the original image to determin this value.