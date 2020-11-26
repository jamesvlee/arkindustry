from flask import Blueprint, render_template
from flask_login import login_required


mod = Blueprint('character', __name__)


@mod.route('/character', methods=['GET'])
@login_required
def character():
    return render_template('character/character.html')
