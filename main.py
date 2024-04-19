import base64
from pathlib import Path
import re
import telebot
from telebot import types
import sqlite3
import requests
import os
import random
from PIL import Image
from rembg import remove
counter_review = 0


bot = telebot.TeleBot('YOURBOT:TOKEN')
counter = 0
@bot.message_handler(commands = ['start'])
def main(message):
    bot.send_message(message.chat.id, 'Привет! Я - виртуальный помощник-стилист. Моя главная задача в этом мире - помочь тебе подобрать стильный лук.')
    conn = sqlite3.connect('Stylist.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, name varchar(50), phone_number varchar(50))')
    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS images'
                ' (image_id integer primary key autoincrement, '
                'image varchar(200), category varchar(50), '
                'subcategory varchar(50), '
                'style varchar(50), '
                'user_id int not null, '
                'FOREIGN KEY (user_id) REFERENCES users (id))')

    conn.commit()
    cur.execute('CREATE TABLE IF NOT EXISTS reviews (review_id integer primary key autoincrement, review_text text(300), user_id int not null, FOREIGN KEY (user_id) REFERENCES users (id))')
    conn.commit()
    info = cur.execute('SELECT * FROM users WHERE name=?', (message.from_user.username, )).fetchone()
    if info is None:
        bot.send_message(message.chat.id, 'Для использования бота необходимо прохождение регистрации с помощью номера телефона. Введите ваш номер телефона')
        bot.register_next_step_handler(message, phone_number)
    cur.close()
    conn.close()

_user_id = ''
def phone_number(message):
    if message.content_type == 'text':
        number = message.text.strip()
        result = re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', number)
        if not result:
            bot.send_message(message.chat.id, 'Ваше сообщение не является номером телефона. Пожалуйста, введите номер')
            bot.register_next_step_handler(message, phone_number)
        else:
            bot.send_message(message.chat.id, 'Принято!')
            conn = sqlite3.connect('Stylist.sql')
            cur = conn.cursor()
            cur.execute("INSERT INTO users (id, name, phone_number) VALUES ('%s', '%s', '%s')" % (message.from_user.id, message.from_user.username, number))
            conn.commit()
            cur.close()
            conn.close()
            global _user_id
            _user_id = message.from_user.id
            bot.send_message(message.chat.id, 'Вы зарегистрированы!')
            bot.send_message(message.chat.id, 'Введите команду /menu, чтобы просмотреть список команд')
    else:
        bot.send_message(message.chat.id, 'Ваше сообщение не является номером телефона. Пожалуйста, введите номер')
        bot.register_next_step_handler(message, phone_number)


@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Добавить вещи')
    btn2 = types.KeyboardButton('Собрать образ')
    btn3 = types.KeyboardButton('Просмотреть вещи')
    btn4 = types.KeyboardButton('Оставить отзыв')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    bot.send_message(message.chat.id,'Что вы хотите сделать?', reply_markup=markup)
    bot.register_next_step_handler(message, on_click)

arr = []
def on_click(message):
   if message.content_type == 'text' and message.text == 'Добавить вещи':
       arr.clear()
       markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
       btn1 = types.KeyboardButton('Одежда')
       btn2 = types.KeyboardButton('Аксессуары')
       btn3 = types.KeyboardButton('Рюкзаки, Сумки')
       btn4 = types.KeyboardButton('Обувь')
       markup.row(btn1, btn2)
       markup.row(btn3, btn4)
       bot.send_message(message.chat.id, 'Фотографируйте светлые вещи на тёмном фоне, а тёмные на светлом')
       bot.send_message(message.chat.id, 'Выберите категорию вещей, которые вы хотите добавить', reply_markup=markup)
       bot.register_next_step_handler(message, things)
   elif message.content_type == 'text' and message.text == 'Просмотреть вещи':
       markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
       conn = sqlite3.connect('Stylist.sql')
       cur = conn.cursor()
       us_id = cur.execute('SELECT * FROM users').fetchall()
       us_id = cur.execute('SELECT * FROM images').fetchall()
       images = cur.execute(f'SELECT image FROM images WHERE user_id={message.from_user.id}').fetchall()
       if len(images) == 0:
           markup_ = types.ReplyKeyboardRemove()
           bot.send_message(message.chat.id, 'У вас пока нет добавленных вещей!', reply_markup = markup_)
           cur.close()
           conn.close()
       else:
           markup_ = types.ReplyKeyboardRemove()
           bot.send_message(message.chat.id, 'Сейчас отправим!', reply_markup=markup_)
           for image in images:
               print(image[0])
               with open(image[0], 'rb') as f:
                   bot.send_photo(message.chat.id, f)
           cur.close()
           conn.close()
   elif message.content_type == 'text' and message.text == 'Оставить отзыв':
       markup_ = types.ReplyKeyboardRemove()
       bot.send_message(message.chat.id, 'Напишите отзыв', reply_markup=markup_)
       bot.register_next_step_handler(message, user_review)
   elif message.content_type == 'text' and message.text == 'Собрать образ':
       conn = sqlite3.connect('Stylist.sql')
       cur = conn.cursor()
       images = cur.execute(f'SELECT image FROM images WHERE user_id={message.from_user.id}').fetchall()
       if len(images) == 0:
           markup_ = types.ReplyKeyboardRemove()
           bot.send_message(message.chat.id, 'У вас нет загруженных фотографий. Воспользуйтесь функцией “Добавить вещи”', reply_markup=markup_)
           cur.close()
           conn.close()
       else:
           markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
           btn1 = types.KeyboardButton('Повседневный')
           btn2 = types.KeyboardButton('Деловой')
           btn3 = types.KeyboardButton('Вечерний')
           btn4 = types.KeyboardButton('Спортивный')
           markup.row(btn1, btn2)
           markup.row(btn3, btn4)
           bot.send_message(message.chat.id, 'Выберите стиль, который вам нужен:', reply_markup=markup)
           bot.register_next_step_handler(message, make_style)
   elif message.content_type == 'text' and message.text == '/menu':
       menu(message)
   elif message.content_type == 'text' and message.text == '/start':
       main(message)
   else:
       error(message, on_click)


def make_style(message):
    if message.content_type == 'text' and message.text in ['Повседневный', 'Деловой', 'Вечерний', 'Спортивный']:
        _style = message.text
        conn = sqlite3.connect('Stylist.sql')
        cur = conn.cursor()
        images = cur.execute(f'SELECT image, category, subcategory, style FROM images WHERE user_id={message.from_user.id}').fetchall()
        false_markup = types.ReplyKeyboardRemove()
        false_text = 'У вас нет достаточного количества элементов одежды выбранного стиля. Воспользуйтесь функцией “Добавить вещи”'
        my_dict = {
            "up": [False, []],
            "down": [False, []],
            "dress": [False, []],
            "shoes": [False, []],
            "backpacks": [False, ['']],
            "acc": [False, ['']]
        }
        up = ['Верхняя одежда', 'Футболки и Лонгсливы', 'Толстовки и Худи', 'Кардиганы и Свитеры', 'Рубашки и Блузы',
              'Пиджаки']
        down = ['Брюки и Джинсы', 'Юбки и Шорты', 'Леггинсы и Белье']
        dress = 'Платья'
        for image in images:
            if image[-1] == _style and image[1] == 'Обувь':
                my_dict["shoes"][0] = True
                my_dict["shoes"][1].append(image[0])
            elif image[-1] == _style and image[2] in up:
                my_dict["up"][0] = True
                my_dict["up"][1].append(image[0])
            elif image[-1] == _style and image[2] == dress:
                my_dict["dress"][0] = True
                my_dict["dress"][1].append(image[0])
            elif image[-1] == _style and image[2] in down:
                my_dict["down"][0] = True
                my_dict["down"][1].append(image[0])
            elif image[-1] == _style and image[1] == 'Рюкзаки, Сумки':
                my_dict["backpacks"][0] = True
                my_dict["backpacks"][1].append(image[0])
            elif image[-1] == _style and image[1] == 'Аксессуары':
                my_dict["acc"][0] = True
                my_dict["acc"][1].append(image[0])
        cur.close()
        conn.close()
        if my_dict["shoes"][0] == False or ((my_dict["up"][0] == False) and (my_dict["dress"][0] == False)) or ((my_dict["dress"][0] == False) and my_dict["down"][0] == False):
            bot.send_message(message.chat.id, false_text, reply_markup=false_markup)
            return
        random_shoes = random.randint(0, len(my_dict["shoes"][1]) - 1)
        random_back, random_acc = '', ''
        img_shoes = Image.open(my_dict["shoes"][1][random_shoes])
        img_shoes = img_shoes.resize((400, 400))
        if my_dict["up"][0] and my_dict["down"][0]:
            random_up = random.randint(0, len(my_dict["up"][1]) - 1)
            random_down = random.randint(0, len(my_dict["down"][1]) - 1)
            img_up = Image.open(my_dict["up"][1][random_up])
            img_down = Image.open(my_dict["down"][1][random_down])
        else:
            random_up = random.randint(0, len(my_dict["dress"][1]) - 1)
            random_down = ''
            img_up = Image.open(my_dict["dress"][1][random_up])
            img_down = ''
        img_up = img_up.resize((400, 400))
        if random_down != '':
            img_down = img_down.resize((400, 400))
        if my_dict["acc"][0]:
            random_acc = random.randint(0, len(my_dict["acc"][1]) - 1)
            if random_acc != 0:
                img_acc = Image.open(my_dict["acc"][1][random_acc])
                img_acc = img_acc.resize((400, 400))
            else:
                random_acc = ''
        if my_dict["backpacks"][0]:
            random_back = random.randint(0, len(my_dict["backpacks"][1]) - 1)
            if random_back != 0:
                img_back = Image.open(my_dict["backpacks"][1][random_back])
                img_back = img_back.resize((400, 400))
            else:
                random_back = ''
        new_image = Image.new('RGB', (3 * img_shoes.size[0], 2 * img_shoes.size[1]), (250, 250, 250))
        new_image.paste(img_up, (0, 0))
        new_image.paste(img_shoes, (800, 0))
        if random_down != '':
            new_image.paste(img_down, (400, 400))
        if random_back != '':
            new_image.paste(img_back, (800, 400))
        if random_acc != '':
            new_image.paste(img_acc, (0, 400))
        bot.send_photo(message.chat.id, new_image)
        choose(message)
    elif message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    else:
        error(message, make_style)

def choose(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('ДАААААА')
    btn2 = types.KeyboardButton('НЕЕЕЕЕЕЕЕТ')
    markup.row(btn1, btn2)
    bot.send_message(message.chat.id, 'Понравился образ?', reply_markup=markup)
    bot.register_next_step_handler(message, answww)
def answww(message):
    if message.content_type == 'text' and message.text == 'ДАААААА':
        bot.send_message(message.chat.id, 'Спасибо за использование', reply_markup=types.ReplyKeyboardRemove())
    elif message.content_type == 'text' and message.text == 'НЕЕЕЕЕЕЕЕТ':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Повседневный')
        btn2 = types.KeyboardButton('Деловой')
        btn3 = types.KeyboardButton('Вечерний')
        btn4 = types.KeyboardButton('Спортивный')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        bot.send_message(message.chat.id, 'Попробуем ещё раз. Выберите желаемый стиль образа', reply_markup=markup)
        bot.register_next_step_handler(message, make_style)
    elif message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    else:
        error(message, answww)



def error(message, command):
    bot.send_message(message.chat.id,'Вы прислали что-то другое. Пожалуйста, выберите один из предложенных вариантов ответа или вернитесь в меню')
    bot.register_next_step_handler(message, command)

def user_review(message):
    if message.content_type == 'text' and message.text != '/start' and message.text != '/menu':
        review = message.text
        conn = sqlite3.connect('Stylist.sql')
        cur = conn.cursor()
        global _user_id
        cur.execute("INSERT INTO reviews (review_text, user_id) VALUES ('%s', '%s')" % (review, message.from_user.id))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, 'Спасибо за обратную связь!')
        conn = sqlite3.connect('Stylist.sql')
        cur = conn.cursor()
    elif message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    else:
        bot.send_message(message.chat.id, 'Вместо текста-отзыва вы прислали что-то другое. Пожалуйста, пришлите текстовый отзыв.')
        bot.register_next_step_handler(message, user_review)

def things(message):
    global arr
    if message.content_type == 'text' and message.text == 'Одежда':
        arr.append(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Верхняя одежда')
        btn2 = types.KeyboardButton('Футболки и Лонгсливы')
        btn3 = types.KeyboardButton('Толстовки и Худи')
        btn4 = types.KeyboardButton('Кардиганы и Свитеры')
        btn5 = types.KeyboardButton('Брюки и Джинсы')
        btn6 = types.KeyboardButton('Платья')
        btn7 = types.KeyboardButton('Пиджаки')
        btn8 = types.KeyboardButton('Юбки и Шорты')
        btn9 = types.KeyboardButton('Рубашки и Блузы')
        btn10 = types.KeyboardButton('Леггинсы и Белье')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        markup.row(btn5, btn6)
        markup.row(btn7, btn8)
        markup.row(btn9, btn10)
        bot.send_message(message.chat.id, 'Выберите подкатегорию вашей одежды', reply_markup=markup)
        bot.register_next_step_handler(message, style)
    elif message.content_type == 'text' and message.text == 'Аксессуары':
        arr.append(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Шапки, Платки, Шляпы')
        btn2 = types.KeyboardButton('Шарфы')
        btn3 = types.KeyboardButton('Перчатки')
        btn4 = types.KeyboardButton('Галстуки и Бабочки')
        btn5 = types.KeyboardButton('Ремни')
        btn6 = types.KeyboardButton('Бижутерия')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        markup.row(btn5, btn6)
        bot.send_message(message.chat.id, 'Выберите подкатегорию ваших аксессуаров', reply_markup=markup)
        bot.register_next_step_handler(message, style)
    elif message.content_type == 'text' and message.text == 'Обувь':
        arr.append(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Туфли')
        btn2 = types.KeyboardButton('Сапоги')
        btn3 = types.KeyboardButton('Ботинки и Полуботинки')
        btn4 = types.KeyboardButton('Кеды и Кроссовки')
        btn5 = types.KeyboardButton('Сандалии, Босоножки, Шлепанцы')
        markup.row(btn1, btn2)
        markup.row(btn3)
        markup.row(btn4)
        markup.row(btn5)
        bot.send_message(message.chat.id, 'Выберите подкатегорию вашей обуви', reply_markup=markup)
        bot.register_next_step_handler(message, style)
    elif message.content_type == 'text' and message.text == 'Рюкзаки, Сумки':
        arr.append(message.text)
        style(message)
    elif message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    else:
        error(message, things)


def style(message):
    global arr
    if message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    elif message.content_type == 'text' and ((arr[-1] == 'Одежда' and message.text in [
        'Верхняя одежда',  'Футболки и Лонгсливы', 'Толстовки и Худи',
        'Кардиганы и Свитеры', 'Брюки и Джинсы', 'Платья', 'Пиджаки',
        'Юбки и Шорты','Рубашки и Блузы','Леггинсы и Белье']) or
         (arr[-1] == 'Аксессуары' and message.text in ['Шапки, Платки, Шляпы',
         'Шарфы', 'Перчатки', 'Галстуки и Бабочки', 'Ремни', 'Бижутерия' ]) or
         (arr[-1] == 'Обувь' and message.text in ['Туфли', 'Сапоги', 'Ботинки и Полуботинки',
         'Кеды и Кроссовки', 'Сандалии, Босоножки, Шлепанцы'])
        or message.text == 'Рюкзаки, Сумки'):
        arr.append(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Повседневный')
        btn2 = types.KeyboardButton('Деловой')
        btn3 = types.KeyboardButton('Вечерний')
        btn4 = types.KeyboardButton('Спортивный')
        markup.row(btn1, btn2)
        markup.row(btn3, btn4)
        bot.send_message(message.chat.id, 'Выберите стиль данной вещи', reply_markup=markup)
        bot.register_next_step_handler(message, type_photo)
    else:
        error(message, style)

def type_photo(message):
    if message.content_type == 'text' and message.text == '/menu':
        menu(message)
    elif message.content_type == 'text' and message.text == '/start':
        main(message)
    elif message.content_type == 'text' and message.text in ['Повседневный', 'Деловой', 'Вечерний', 'Спортивный']:
        global arr
        arr.append(message.text)
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, 'Загрузите фото', reply_markup=markup)
        bot.register_next_step_handler(message, get_photo)
    else:
        error(message, type_photo)

file_info = ''
counter = 0

def get_photo(message):
    global file_info
    if message.content_type == 'text' and message.text == '/start':
        main(message)
    elif message.content_type == 'text' and message.text == '/menu':
        menu(message)
    else:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Удалить фото', callback_data='delete')
            btn2 = types.InlineKeyboardButton('Внести фото в базу', callback_data='done')
            markup.row(btn2, btn1)

            bot.send_message(message.chat.id, 'Фото будет внесено в базу', reply_markup=markup)
            bot.register_next_step_handler(message, callback_message)
        except:
            bot.send_message(message.chat.id, 'Вместо фотографии пришло что-то другое. Пришлите фото, пожалуйста')
            bot.register_next_step_handler(message, get_photo)


@bot.callback_query_handler(func = lambda callback:True)
def callback_message(callback):
    try:
        if callback.data == 'delete':
            bot.delete_message(callback.message.chat.id, callback.message.message_id - 2)
            bot.delete_message(callback.message.chat.id, callback.message.message_id - 1)
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, 'Загрузите новое фото или вернитесь в /menu')
            bot.register_next_step_handler(callback.message, get_photo)
            #bot.clear_step_handler_by_chat_id(chat_id=callback.message.chat.id)
        elif callback.data == 'done':
            global file_info
            global _user_id
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, 'Дождитесь загрузки, пожалуйста')
            conn = sqlite3.connect('Stylist.sql')
            cur = conn.cursor()
            downloaded_file = bot.download_file(file_info.file_path)
            src = f'photos/{callback.from_user.id}/';
            if os.path.exists(src) is False:
                os.mkdir(src)
            id_ = cur.execute('SELECT image_id FROM images').fetchall()
            if len(id_) == 0:
                counter = 1
            else:
                counter = id_[-1][0] + 1
            src = src + str(counter) + '.jpg'
            with open(src, 'wb') as new_file:
                # записываем данные в файл
                new_file.write(remove(downloaded_file))

            cur.execute("INSERT INTO images (image, category, subcategory, style, user_id) VALUES ('%s', '%s', '%s', '%s', '%s')"
                        % (src, arr[0], arr[1], arr[2], callback.from_user.id))
            conn.commit()
            cur.close()
            conn.close()
            bot.send_message(callback.message.chat.id, 'Фото внесено в базу')
            arr.clear()
            bot.delete_message(callback.message.chat.id, callback.message.message_id + 1)
            bot.clear_step_handler_by_chat_id(chat_id=callback.message.chat.id)
    except:
        bot.register_next_step_handler(callback, callback_message)

bot.polling(none_stop=True)
