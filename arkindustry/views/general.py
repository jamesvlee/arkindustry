from flask import Blueprint, request, render_template, redirect, url_for, g, abort
from arkindustry import app
from arkindustry.database import create_member, MiningChannel, Member
from arkindustry.forms import RegistrationForm, LoginForm, EmailForm, PasswordForm
from flask_login import login_required, login_user, logout_user, current_user
from arkindustry.util import ts, send_email
from werkzeug.security import generate_password_hash

import datetime


global_var = [0]

def set_var(var):
    global_var[0] = var

def get_var():
    return global_var[0]

def get_domain():
    return app.config['DOMAIN']

app.add_template_global(set_var, 'set_var')
app.add_template_global(get_var, 'get_var')
app.add_template_global(get_domain, 'get_domain')

@app.before_request
def cal__copyright():
    year = datetime.datetime.now().year
    started = app.config['STARTED']
    copyright = str(started)
    if year > started:
        copyright = '2020-{}'.format(year)
    set_var(copyright)


@app.errorhandler(404)
def not_found(e):
    return render_template('error/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error/403.html'), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error/500.html'), 500


@app.before_request
def load_user():
    if current_user:
        g.user = current_user


mod = Blueprint('general', __name__)


@mod.route('/', methods=['GET'])
def index():
    return render_template('general/index.html')

@mod.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    error_msg = None
    if request.method == 'POST' and form.validate():
        email = form.email.data
        nickname = form.nickname.data.strip()
        password = form.password.data
        try:
            if Member.nick_exist(nickname):
                raise
            if not create_member(email, nickname, password):
                return abort(400)
            return redirect(url_for('general.login'))
        except:
            error_msg = '此昵称已存在'
    return render_template('general/register.html', form=form, error_msg=error_msg)


@mod.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    error_msg = None
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = form.remember.data
        member = Member.get_member(email)
        if not member:
            error_msg = '邮箱或密码输入有误'
        else:
            if member.verify_password(password):
                login_user(member, remember=remember)
                return redirect(url_for('general.index'))
            else:
                error_msg = '邮箱或密码输入有误'
    return render_template('general/login.html', form=form, error_msg=error_msg)


@mod.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('general.index'))


@mod.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = EmailForm()
    error_msg = None
    if form.validate_on_submit():
        email = form.email.data
        member = Member.get_member(email=email)
        if not member:
            error_msg = '该邮箱对应的用户不存在'
        else:
            subject = '密码重置 - 方舟工业ArkIndustry'
            token = ts.dumps(email, salt=app.config['SALT'])
            recover_url = url_for(
                'general.reset_password_with_token',
                token=token,
                _external=True)
            html = render_template(
                'email/recover_password.html',
                recover_url=recover_url)
            send_email(email, subject, html)
            return redirect(url_for('general.please_check_your_email'))
    return render_template('general/reset_password.html', form=form, error_msg=error_msg)


@mod.route('/please_check_your_email', methods=['GET'])
def please_check_your_email():
    return render_template('general/please_check_your_email.html')


@mod.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_with_token(token):
    try:
        email = ts.loads(token, salt=app.config['SALT'], max_age=86400)
    except:
        abort(404)
    form = PasswordForm()
    if form.validate_on_submit():
        Member.objects(email=email).update_one(set__password=generate_password_hash(form.password.data))
        return redirect(url_for('general.password_reset_success'))
    return render_template('general/please_set_your_new_password.html', form=form, token=token)


@mod.route('/password_reset_success', methods=['GET'])
def password_reset_success():
    return render_template('general/password_reset_success.html')


@mod.route('/recover_password', methods=['GET'])
def recover_password():
    return render_template('email/recover_password.html')
