import smtplib
import re
import functools
import random
import sqlite3
import urllib

import telebot
from telebot import types
from telebot.types import ReplyKeyboardRemove

from settings import TOKEN, ADMIN_ID
from email_config import send_contact_email
from questions_answers import answers, questions, animal_responses, animals_photos
from logger import logger, log_errors, log_performance
from buttons import (quiz_button, guardian_button, contact_button, feedback_button,
                     menu_button, yes_button, search_more_button, quiz_inquiry_button)
from dbutils.pooled_db import PooledDB

bot = telebot.TeleBot(TOKEN)

db_pool = PooledDB(sqlite3, maxconnections=10, database='quiz_results.db')


@log_errors
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(quiz_button, guardian_button, contact_button, feedback_button)
    file_path = 'logo/Mzoo-logo-01.webp'
    with open(file_path, 'rb') as logo:
        bot.send_photo(message.chat.id, logo, 'Мяуу Пррривет, ' + str(message.from_user.first_name) + '!'
                                              '\nЯ кот-бот. Добро пожаловать в бот Московского Зоопарка!'
                                              '\nДавай узнаем что-то новое!',
                       reply_markup=markup)


@log_errors
@bot.callback_query_handler(func=lambda call: call.data in ['quiz', 'become-a-guardian', 'contact', 'feedback'])
def callback_query1(call):
    if call.data == 'quiz':
        start_quiz(call.message)

    elif call.data == 'become-a-guardian':
        with open('become-a-guardian.txt', 'r', encoding='utf-8') as file:
            program_text = file.read()
            bot.send_message(call.message.chat.id, program_text, parse_mode='HTML')

            message_text = ("Узнать больше о программе <a href='https://moscowzoo.ru/my-zoo/become-a-guardian/'>"
                            "«Возьми животное под опеку»</a>")
            markup = types.InlineKeyboardMarkup(row_width=1)
            markup.add(menu_button)
            bot.send_message(call.message.chat.id, message_text, reply_markup=markup, parse_mode='HTML')

    elif call.data == 'contact':
        handle_contact(call.message)

    elif call.data == 'feedback':
        handle_feedback_query(call.message)


@bot.message_handler(commands=['quiz'])
def start_quiz(message):
    file_path = 'logo/quiz_logo-01.webp'
    with open(file_path, 'rb') as logo:
        bot.send_photo(message.chat.id, logo)
    bot.send_message(message.chat.id, 'Мяуу! Узнаем, кто твое животное-хранитель!\nОтветь на следующие вопросы:')
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)

    for answer in answers[0]:
        markup.add(types.KeyboardButton(answer))
    bot.send_message(message.chat.id, questions[0], reply_markup=markup)
    bot.register_next_step_handler(message, functools.partial(handle_quiz_process, user_answers=[]))


@log_errors
def validate_answer(message, user_answers):
    if message.text not in answers[len(user_answers)]:
        logger.error('Invalid answer from user: %s', message.text)
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, '🐷Ошибка! Пожалуйста, используй кнопки.')
        return False
    return True


def send_question(message, user_answers):
    current_question = len(user_answers)
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for answer in answers[current_question]:
        markup.add(types.KeyboardButton(answer))
    bot.send_message(message.chat.id, questions[current_question], reply_markup=markup)
    bot.register_next_step_handler(message, functools.partial(handle_quiz_process, user_answers=user_answers))


def calculate_scores(user_answers):
    animal_scores = {"Кряква": 0, "Королевская кобра": 0, "Камышовый кот": 0}
    for i, user_answer in enumerate(user_answers):
        animal = animal_responses[i][answers[i].index(user_answer)]
        animal_scores[animal] += 1
    return animal_scores


def store_quiz_result(result_animal):
    conn = db_pool.connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO quiz_results (result_animal) VALUES (?)", (result_animal,))
            conn.commit()
    finally:
        conn.close()


def generate_whatsapp_share_text(result_animal):
    share_text = f"https://t.me/AnimalQuizBot Смотри, мое тотемное животное - {result_animal}!"
    share_link = f"https://wa.me/?text={urllib.parse.quote(share_text)}"
    return share_link


@log_errors
def handle_quiz_process(message, user_answers):
    if not validate_answer(message, user_answers):
        send_question(message, user_answers)
        return

    user_answers.append(message.text)
    current_question = len(user_answers)

    if current_question < len(questions):
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        for answer in answers[current_question]:
            markup.add(types.KeyboardButton(answer))
        bot.send_message(message.chat.id, questions[current_question], reply_markup=markup)
        bot.register_next_step_handler(message, functools.partial(handle_quiz_process, user_answers=user_answers))

    else:
        animal_scores = calculate_scores(user_answers)
        max_score = max(animal_scores.values())
        top_animals = [animal for animal, score in animal_scores.items() if score == max_score]
        result_animal = random.choice(top_animals)

        store_quiz_result(result_animal)

        photo_path = 'photos/' + animals_photos[result_animal]
        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)

        result_message = f"Поздравляю! Твое тотемное животное - {result_animal}!"
        bot.send_message(message.chat.id, result_message)

        share_text = 'Поделись результатом викторины с друзьями!'
        switch_query = f'\nМое животное-хранитель - это {result_animal}'
        whatsapp_share_link = generate_whatsapp_share_text(result_animal)
        markup = types.InlineKeyboardMarkup(row_width=2)
        telegram_share_button = types.InlineKeyboardButton('В Телеграмм!',
                                                           switch_inline_query=switch_query)
        whatsapp_share_button = types.InlineKeyboardButton('В WhatsApp!', url=whatsapp_share_link)
        markup.add(telegram_share_button, whatsapp_share_button, quiz_inquiry_button)
        bot.send_message(message.chat.id, share_text, reply_markup=markup)

        markup = types.ReplyKeyboardMarkup(row_width=2)
        markup.add(yes_button, search_more_button)
        bot.send_message(message.chat.id, f"Хочешь стать опекуном твоего животного-хранителя {result_animal}?",
                         reply_markup=markup)
        bot.register_next_step_handler(message, program_info)


@log_errors
def program_info(message):
    if message.text == 'Да':
        message_text = ("Узнать о программе <a href='https://moscowzoo.ru/my-zoo/become-a-guardian/'>"
                        "«Возьми животное под опеку»</a>")
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(menu_button)
        bot.send_message(message.chat.id, message_text, reply_markup=markup, parse_mode='HTML')
    elif message.text == 'Нет, искать еще!':
        start_quiz(message)


@bot.callback_query_handler(func=lambda call: call.data == 'menu')
def return_to_menu(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(quiz_button, guardian_button, contact_button, feedback_button)
    file_path = 'logo/Mzoo-logo-01.webp'
    with open(file_path, 'rb') as logo:
        bot.send_photo(call.message.chat.id, logo, 'Мяуу! Ну что, сыграем?', reply_markup=markup)


@bot.message_handler(commands=['contact'])
def handle_contact(message):
    contact_zoo(message)


@bot.callback_query_handler(func=lambda call: call.data == 'quiz_inquiry')
def handle_inquiry_callback(call):
    contact_zoo(call.message)


def contact_zoo(message):
    bot.send_message(message.chat.id, 'Мяуу, введи адрес эл.почты для обратной связи: ')
    bot.register_next_step_handler(message, get_user_email)


@log_errors
def get_user_email(message):
    user_email = message.text

    if not re.match(r'[^@]+@[^@]+\.[^@]+', user_email):
        bot.send_message(message.chat.id, 'Мяуу, такой адрес почты мы, 🐱 коты 🐱, не понимаем \n'
                                          'Пожалуйста, используй корректный формат (например, username@yandex.ru): ')
        bot.register_next_step_handler(message, get_user_email)
        return
    bot.send_message(message.chat.id, 'Напиши сообщение: ', reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, functools.partial(handle_contact_inquiry, user_email=user_email))


@log_errors
@log_performance
def handle_contact_inquiry(message, user_email):
    user_message = message

    # Получаем результат викторины из ДБ
    conn = sqlite3.connect('quiz_results.db')
    c = conn.cursor()
    c.execute("SELECT result_animal FROM quiz_results ORDER BY id DESC LIMIT 1")
    result_row = c.fetchone()
    if result_row:
        result_animal = result_row[0]
    else:
        result_animal = "Еще нет результата"

    try:
        send_contact_email(user_message, user_email, result_animal)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(menu_button)
        bot.send_message(message.chat.id, 'Сообщение успешно отправлено!', reply_markup=markup)

        c.execute('DELETE FROM quiz_results')
        conn.commit()
        conn.close()

    except smtplib.SMTPSenderRefused as ex:
        logger.error(f'SMTP sender refused error: {ex}')
        bot.send_message(message.chat.id, f'Ошибка при отправке сообщения: {ex}. '
                                          f'Пожалуйста, введи другой адрес эл.почты.')
        bot.register_next_step_handler(message, get_user_email)

    except sqlite3.Error as ex:
        logger.error(f'SQLite error: {ex}')
        bot.send_message(message.chat.id, 'Произошла ошибка при обработке запроса. Попробуйте позже.')

    except Exception as ex:
        logger.error(f'An error occurred in handle_contact_inquiry: {ex}')
        bot.send_message(message.chat.id, 'Произошла неизвестная ошибка. Попробуйте позже.')


@bot.message_handler(commands=['feedback'])
def handle_feedback_query(message):
    bot.send_message(message.chat.id, 'Мяуу!\nПиши свой отзыв внизу', reply_markup=feedback_button)
    bot.register_next_step_handler(message, handle_feedback_message)


@log_errors
@log_performance
def handle_feedback_message(message):
    feedback = message.text
    logger.info(f'Новый отзыв от пользователя {message.from_user.username} id: {message.from_user.id} : {feedback}')
    bot.send_message(ADMIN_ID, f'Новый отзыв от {message.from_user.id}:\n{feedback}')

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(menu_button)
    bot.send_message(message.chat.id, 'Спасибо! Твое сообщение было передано администратору.', reply_markup=markup)


available_commands = [
    "/start - Начать взаимодействие с ботом",
    "/quiz - Начать викторину",
    "/contact - Написать специалисту зоопарка",
    "/feedback - Оставить отзыв о боте"
]


@bot.message_handler(func=lambda message: message.text.startswith("/") and not any(
    message.text.split()[0].split("@")[0][1:] in command for command in available_commands))
def wrong_command(message):
    bot.send_message(message.chat.id, "🙈 Неверная команда! Пожалуйста, выберите одну из доступных команд:"
                                      "\n\n" + "\n".join(available_commands))


@bot.message_handler(content_types=['document', 'photo', 'video', 'video_note', 'sticker', 'voice'],
                     func=lambda message: True)
def answer_on_media(message):
    bot.send_message(message.chat.id, 'Я принимаю только текстовые сообщения')


if __name__ == '__main__':
    bot.polling(non_stop=True)
