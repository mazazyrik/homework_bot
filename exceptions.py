class APIRequestException(Exception):
    """Исключение для ответа API."""

    pass


def api_error(status_code):
    """Ошибка, вызываемая если код ответа не 200."""
    if status_code != 200:
        raise APIRequestException('Код ответа API не 200')
