from flask import Blueprint, request
from arkindustry.database import Fleet, Mining, Production
from flask_login import current_user


mod = Blueprint('general', __name__)


@mod.route('/mining/build_a_fleet/', methods=['POST'])
@login_required
def build_a_fleet():
    fleet = Fleet(createdby=current_user, usage=Mining())


@mod.route('/mining/fleet/<int:fleet_id>/caculate_production/', methods=['POST'])
@login_required
def caculate_production():
    pick_up_record = request.form['pur']
    personal_pur = list()
    productions = list()
    for pur in personal_pur:
        member = Member()
        volume = 0
        production = Production(member=member, volume=volume)
        productions.append(production)
    total_volume = 0
    fleet = get_fleet_by_fleet_id(fleet_id)
    fleet.usage.total_volume = total_volume
    fleet.usage.productions = productions


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        nickname = form.nickname.data
        password = form.password.data
        if not create_member(email, nickname, password):
            return abort(400)
        return redirect(url_for('general.index'))
    return render_template('general/register.html', form=form)


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    error_msg = None
    if form.validate_on_submit():
        email = form.email.data
        password = form.pasword.data
        remember = form.remember.data
        member = Member.get_member(email)
        if not member:
            error_msg = '邮箱或密码有误'
        else:
            if member.verify_password(password):
                login_user(member, remember=remember)
                return redirect(url_for('general.index'))
            else:
                error_msg = '邮箱或密码有误'
    return render_template('general/login.html', form=form, error_msg=error_msg)


@mod.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
