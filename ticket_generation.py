from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg


TICKET_PATTERN_PATH = './files/ticket_form.png'
FONT_PATH = './files/Roboto-Regular.ttf'
FONT_SIZE = 40
BLACK = (0, 0, 0, 255)
DEP_CITY_OFFSET = (540, 300)
DES_CITY_OFFSET = (510, 385)
DATE_OFFSET = (395, 500)
AVATAR_OFFSET = (1000, 300)
AVATAR_SIZE = (250, 250)


def generate_ticket(dep_city, des_city, date, phone_number):
    """
    Генерация изображения билета
    :param dep_city: город отправления
    :param des_city: город назначения
    :param date: дата отправления
    :param phone_number: номер телефона
    :return: файл изображения
    """
    base = Image.open(TICKET_PATTERN_PATH)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base)
    draw.text(DEP_CITY_OFFSET, dep_city, font=font, fill=BLACK)
    draw.text(DES_CITY_OFFSET, des_city, font=font, fill=BLACK)
    draw.text(DATE_OFFSET, date, font=font, fill=BLACK)

    response = requests.get(f'https://avatars.dicebear.com/api/avataaars/{phone_number}.svg')
    avatar_file_like = BytesIO(response.content)
    drawing = svg2rlg(avatar_file_like)
    png = BytesIO()
    renderPM.drawToFile(drawing, png, fmt='PNG')
    avatar = Image.open(png)
    avatar = avatar.resize(AVATAR_SIZE)
    old_size = avatar.size
    new_size = tuple(map(lambda x: x + 10, AVATAR_SIZE))
    new_im = Image.new("RGB", new_size)
    new_im.paste(avatar, ((new_size[0] - old_size[0]) // 2, (new_size[1] - old_size[1]) // 2))

    avatar = new_im
    base.paste(avatar, AVATAR_OFFSET)
    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


if __name__ == '__main__':
    a = generate_ticket('Москва', 'Петербург', '10-12-2021', '89375647385')