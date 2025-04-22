from typing import Optional

import requests
from django.core.files.base import ContentFile

from users.models import User


def set_avatar_from_url(user: User, image_url: str, default_filename: Optional[str] = None) -> None:
    """
    Загружает изображение с указанного URL и устанавливает его как аватар пользователя.
    https://robohash.org/username?bgset=bg1&set=set4&size=50x50
    """
    response = requests.get(image_url)
    if response.status_code != 200:
        raise ValueError(f"Не удалось загрузить изображение с {image_url}: HTTP {response.status_code}")

    file_name = image_url.split('/')[-1].split('?')[0] or default_filename or 'avatar.jpg'

    if not file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        file_name = f'{user.username}.jpg'

    image_content = ContentFile(response.content, name=file_name)

    user.avatar = image_content  # type: ignore
    user.save(update_fields=['avatar'])

    if not user.avatar:
        raise ValueError("Аватар не был сохранен в поле avatar")
