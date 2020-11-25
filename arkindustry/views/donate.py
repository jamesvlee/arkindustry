from flask import Blueprint, render_template


mod = Blueprint('donate', __name__)


@mod.route('/donate', methods=['GET'])
def donate():
    return render_template('donate/donate.html')
