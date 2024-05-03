from random import randrange


def get_rnd_hex_color():
    """Функция генерации случайного цветового кода."""
    color = randrange(0, 2**24)
    hex_color = hex(color)
    return ("#" + hex_color[2:])
