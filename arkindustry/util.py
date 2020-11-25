from arkindustry import app, mail
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message


ts = URLSafeTimedSerializer(app.config['SECRET_KEY'])


def send_email(recipient, subject, html):
    msg = Message(subject, sender=app.config['MAIL_DEFAULT_SENDER'], recipients=[recipient])
    msg.html = html
    mail.send(msg)
