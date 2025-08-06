import json
import os
import requests
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from urllib.parse import unquote
from django.conf import settings
from apps.categories.models import Category
from apps.products.models import (
    ProductMedia,
    Product
)

def get_hundred_products():
    """ Load product data from JSON file """

    with open(f"{settings.BASE_DIR}/import_products/products.json", "r") as f:
        products = json.loads(f.read())
    return products[:100]

def add_category(category_name):
    """ Add products categories """
    category, created = Category.objects.get_or_create(
        name=category_name,
        defaults={
            "description": category_name
        }
    )
    return category


def determine_extension(file_content):
    """Detect the file type using magic numbers"""
    if file_content.startswith(b'\xFF\xD8\xFF'):
        return 'jpg'
    elif file_content.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif file_content.startswith(b'GIF87a') or file_content.startswith(b'GIF89a'):
        return 'gif'
    elif file_content.startswith(b'RIFF') and file_content[8:12] == b'WEBP':
        return 'webp'
    return 'jpg'

def download_image(image_url):
    """
    Download an image from URL and return File object with correct extension
    Args:
        image_url (str): URL of the image to download
    Returns:
        Tuple (File object, extension) or (None, None) if failed
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Read content to determine actual image type
        content = b''.join([chunk for chunk in response.iter_content(chunk_size=8192)])
        extension = determine_extension(content)

        # Create file with proper extension
        img_temp = NamedTemporaryFile(delete=True, suffix=f'.{extension}')
        img_temp.write(content)
        img_temp.seek(0)

        return File(img_temp), extension

    except Exception as e:
        print(f"Download failed for {image_url}: {str(e)}")
        return None, None


def clean_filename(url, extension):
    """
    Sanitize filename from URL and ensure proper extension
    Args:
        url (str): Original image URL
        extension (str): Detected file extension
    Returns:
        str: Cleaned filename with proper extension
    """
    decoded = unquote(url)
    basename = os.path.basename(decoded.split('?')[0])

    # Replace extension if missing or incorrect
    if not os.path.splitext(basename)[1].lower() in ['.jpg', '.jpeg', '.png', '.webp']:
        basename = f"{os.path.splitext(basename)[0]}.{extension}"

    return basename


def add_product_media(product, media_data):
    """
    Create ProductMedia entry for a product
    Args:
        product (Product): Product instance
        media_data (dict): Media data from JSON
    Returns:
        ProductMedia or None if failed
    """
    if media_data.get("type") != "IMG":
        return None

    image_url = media_data.get("file")
    if not image_url:
        return None

    image_file, extension = download_image(image_url)
    if not image_file:
        return None

    try:
        product_media = ProductMedia(
            product=product,
            title=media_data.get("id", "No title yet.")[:255],  # Respect CharField limit
            description=f"Image for {product.name}"[:500],  # Truncate if too long
        )

        filename = clean_filename(image_url, extension)
        product_media.file.save(filename, image_file, save=True)
        return product_media

    except Exception as e:
        print(f"Failed creating media for {product.name}: {str(e)}")
        return None


def add_products():
    """ Add products and images. """

    for p in get_hundred_products():
        category_name = p.get("dmCategorie")[0]["name"]
        category = add_category(category_name)
        product, created = Product.objects.get_or_create(
            name=p.get("name"),
            defaults={
                "brand": "dm_product",
                "description": p.get("description", "No description"),
                "category": category,
                "price": p.get("original_price", 0)
            }
        )
        if created:
            # Import media only for newly created products
            for media in p.get("medias"):
                add_product_media(product, media)

    print("=== Import completed ===")
    print(f"Products: {Product.objects.count()}")
    print(f"Media files: {ProductMedia.objects.count()}")

if __name__ == "__main__":
    add_products()