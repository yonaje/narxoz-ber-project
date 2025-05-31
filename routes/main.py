
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from flask_wtf import FlaskForm 

class LogoutForm(FlaskForm):
    pass

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    logout_form = LogoutForm() if current_user.is_authenticated else None
    return render_template('index.html', logout_form=logout_form)
