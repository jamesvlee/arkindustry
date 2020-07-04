from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators


class RegistrationForm(FlaskForm):
    email = StringField('邮箱', [validators.DataRequired('需要输入邮箱')])
    nickname = StringField('角色名', [validators.DataRequired('需要输入角色名')])


class LoginForm(FlaskForm):
    email = StringField('邮箱', [validators.DataRequired('需要输入邮箱')])
    password = PasswordField('密码', [validators.DataRequired('需要输入密码')])
