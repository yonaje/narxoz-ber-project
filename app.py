
from dotenv import load_dotenv

load_dotenv()
from flask import Flask, send_from_directory, abort 
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from config import Config
from extensions import db, login_manager, csrf
import os
from sqlalchemy import inspect, text

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'mp3', 'mp4'}
MAX_FILE_SIZE = 25 * 1024 * 1024


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

    db.init_app(app)
    login_manager.init_app(app) 
    csrf.init_app(app)


    login_manager.login_view = 'auth.login'  
    login_manager.login_message = 'Please log in to access this page.' 
    login_manager.login_message_category = 'info'

    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.courses import courses_bp
    from routes.main import main_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp, url_prefix="/students")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(main_bp)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        try:
            upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
            return send_from_directory(upload_dir, filename, as_attachment=False)
        except FileNotFoundError:
             abort(404)

    with app.app_context():
        import models
        db.create_all()

    upload_dir_abs = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir_abs, exist_ok=True)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

