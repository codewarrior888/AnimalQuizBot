from telebot import types


def inline_button(text, callback_data):
    return types.InlineKeyboardButton(text=text, callback_data=str(callback_data))


def keyboard_button(text):
    return types.KeyboardButton(text)


feedback_button = inline_button('Оставить отзыв', callback_data='feedback')

cancel_feedback = inline_button('Отменить отзыв', callback_data='cancel_feedback')

menu_button = inline_button(text='Обратно в меню', callback_data='menu')

quiz_button = inline_button(text='Играть в викторину', callback_data='quiz')

guardian_button = inline_button(text='О Программе опеки животных', callback_data='become-a-guardian')

contact_button = inline_button('Написать специалисту', callback_data='contact')

quiz_inquiry_button = inline_button('Задать вопрос специалисту', callback_data='quiz_inquiry')

yes_button = keyboard_button('Да')

search_more_button = keyboard_button('Нет, искать еще!')
