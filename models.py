
# db models
from datetime import datetime
from extensions import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user 
from sqlalchemy import Text


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(Text, nullable=False)
    courses_created = db.relationship('Course', backref='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    enrollments = db.relationship(
        "Enrollment", backref="student", cascade="all, delete", lazy='dynamic'
    )


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    enrollments = db.relationship("Enrollment", backref="course", cascade="all, delete", lazy='dynamic')
    material_path = db.Column(db.String(255))
    material_summary = db.Column(Text, nullable = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    



class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
    enrolled_on = db.Column(db.DateTime, default=datetime.utcnow)