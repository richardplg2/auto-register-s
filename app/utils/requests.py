import requests


def get_face_image_url_to_bytes(face_image_url: str) -> bytes:
    """Get face image url from http request"""
    response = requests.get(face_image_url)
    response.raise_for_status()
    return response.content
