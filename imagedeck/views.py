from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404


@login_required
def image_upload(request, content_type_id, pk):
    """
    Generic view to take an image (with the keyword 'file') and save it to the image deck of an object.

    It will be saved in the media storage. Returns a json reponse wiht the 'url', the 'thumbnail' url, the width and height of the thumbnail and the caption.
    If the file is not valid, then the 'url' value is an empty string.
    """
    if request.method == "POST" and request.FILES["file"]:
        content_type = get_object_or_404(ContentType, id=content_type_id)
        obj = get_object_or_404(content_type.model_class(), pk=pk)

        uploaded_file = obj.save_image_file(request.FILES["file"])

        width, height = uploaded_file.thumbnail_dimensions()
        data = dict(
            url=uploaded_file.url(),
            thumbnail=uploaded_file.thumbnail(),
            height=height,
            width=width,
            caption=uploaded_file.get_caption(),
        )
    else:
        data = {"url": ""}

    return JsonResponse(data)
