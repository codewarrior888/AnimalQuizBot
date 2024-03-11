import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from logger import log_errors
from settings import MANAGER_EMAIL, USER_EMAIL
import logging

logger = logging.getLogger('AnimalQuizBot')


@log_errors
def send_contact_email(message, user_email, result_animal):
    login = os.getenv("EMAIL_HOST_USER")
    password = os.getenv('EMAIL_HOST_PASSWORD')
    server = smtplib.SMTP_SSL('smtp.yandex.ru', 465)

    try:
        server.login(login, password)
        msg = MIMEMultipart()
        msg['From'] = USER_EMAIL
        msg['To'] = MANAGER_EMAIL
        msg['Subject'] = Header('Вопрос из @AnimalQuizBot', 'utf-8')
        msg.attach(MIMEText(f'<p>Пользователь <strong>{message.from_user.username}</strong> Email: {user_email}</p>'
                            f'\n<p>Результат викторины: {result_animal}</p>'
                            f'\n<p>Сообщение:</p>\n\n<p><em>{message.text}</em></p>',
                            'html'))

        server.sendmail(USER_EMAIL, MANAGER_EMAIL, msg.as_string())
        server.quit()

        logger.info('Email sent successfully!')

    except smtplib.SMTPSenderRefused as _ex:
        logger.exception(f'Failed to send email {_ex}')
        raise
