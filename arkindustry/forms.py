from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, BooleanField, RadioField, FloatField
from wtforms.fields.html5 import EmailField
from arkindustry.database import MINERAL, ORE


class RegistrationForm(FlaskForm):
    email = EmailField('邮箱', [validators.DataRequired(message='需要输入邮箱'),
                                validators.Email(message='请输入正确的邮箱地址')])
    nickname = StringField('角色名', [validators.DataRequired(message='需要输入角色名')])
    password = PasswordField('密码', [validators.DataRequired(message='需要输入密码'),
                                      validators.Length(max=12, min=6, message='密码长度必须为%(min)d到%(max)d')])
    repassword = PasswordField('重复密码', [validators.EqualTo('password', message='两次密码输入不一致')])


class LoginForm(FlaskForm):
    email = EmailField('邮箱', [validators.DataRequired('需要输入邮箱')])
    password = PasswordField('密码', [validators.DataRequired('需要输入密码')])
    remember = BooleanField('记住我')


class EmailForm(FlaskForm):
    email = EmailField('邮箱', [validators.DataRequired(message='需要输入邮箱'),
                                validators.Email(message='请输入正确的邮箱地址')])


class PasswordForm(FlaskForm):
    password = PasswordField('密码', [validators.DataRequired(message='需要输入密码'),
                                      validators.Length(max=12, min=6, message='密码长度必须为%(min)d到%(max)d')])
    repassword = PasswordField('重复密码', [validators.EqualTo('password', message='两次密码输入不一致')])
    

class MiningChannelForm(FlaskForm):
    name = StringField('频道名', [validators.DataRequired('需要输入频道名'),
                                  validators.Length(max=9, min=2, message='频道名长度必须为%(min)d到%(max)d')])


class JoiningMiningChannelForm(FlaskForm):
    name = StringField('频道名', [validators.DataRequired('需要输入频道名')])
    code = StringField('PIN码', [validators.DataRequired('需要输入PIN码')])


class MiningFleetForm(FlaskForm):
    locations = StringField('活动星系', [validators.DataRequired('需要输入矿队活动星系')])


class MineralSettlementForm(FlaskForm):
    ratio = FloatField('结算比例', [validators.NumberRange(0, 100, message='比例必须大于0小于等于100'),
                                    validators.DataRequired('需要输入结算比例')],
                       default=95)
    refining_ratio = FloatField('化矿比例', [validators.NumberRange(0, 100, message='比例必须大于0小于等于100'),
                                             validators.DataRequired('需要输入化矿比例')], default=79)


class OreSettlementForm(FlaskForm):
    ore_ratio = FloatField('结算比例', [validators.NumberRange(0,100, message='比例必须大于0小于等于100'),
                                    validators.DataRequired('需要输入结算比例')],
                       default=95)


class ItemTypeForm(FlaskForm):
    item_name = StringField('物品名称', [validators.DataRequired('需要输入物品名')])
