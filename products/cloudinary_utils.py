import uuid

import cloudinary
import cloudinary.uploader
from django.conf import settings


def _configure_cloudinary():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def _cloudinary_configured():
    return all([
        settings.CLOUDINARY_CLOUD_NAME,
        settings.CLOUDINARY_API_KEY,
        settings.CLOUDINARY_API_SECRET,
    ])


def upload_product_image(image_file, product_id):
    if not _cloudinary_configured():
        raise ValueError(
            'Cloudinary is not configured. Set CLOUDINARY_CLOUD_NAME, '
            'CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET in your environment.'
        )

    _configure_cloudinary()
    folder = f'aharya/products/{product_id}'
    public_id = str(uuid.uuid4())

    result = cloudinary.uploader.upload(
        image_file,
        folder=folder,
        public_id=public_id,
        resource_type='image',
        overwrite=False,
        unique_filename=False,
    )
    return result['secure_url']


def _public_id_from_url(image_url):
    marker = '/upload/'
    if marker not in image_url:
        return None

    suffix = image_url.split(marker, 1)[1]
    segments = suffix.split('/')
    if segments and segments[0].startswith('v') and segments[0][1:].isdigit():
        segments = segments[1:]

    public_id_with_ext = '/'.join(segments)
    filename = public_id_with_ext.rsplit('/', 1)[-1]
    if '.' in filename:
        return public_id_with_ext.rsplit('.', 1)[0]
    return public_id_with_ext


def delete_cloudinary_image(image_url):
    if not image_url or 'cloudinary.com' not in image_url:
        return

    if not _cloudinary_configured():
        return

    public_id = _public_id_from_url(image_url)
    if not public_id:
        return

    _configure_cloudinary()
    try:
        cloudinary.uploader.destroy(public_id, resource_type='image', invalidate=True)
    except Exception:
        pass
