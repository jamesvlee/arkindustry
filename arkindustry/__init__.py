from flask import Flask
from flask_login import LoginManager
from flask_moment import Moment
from flask_mail import Mail


app = Flask(__name__)
app.config.from_object('websiteconfig')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'general.login'

moment = Moment()
moment.init_app(app)

mail = Mail(app)

from arkindustry.views import general,character, mining, market, contract, donate
app.register_blueprint(general.mod)
app.register_blueprint(character.mod)
app.register_blueprint(mining.mod)
app.register_blueprint(market.mod)
app.register_blueprint(contract.mod)
app.register_blueprint(donate.mod)
