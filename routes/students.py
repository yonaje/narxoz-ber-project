
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
try:
    from extensions import db
    from models import Student, Course, Enrollment
except ImportError:
    from ..extensions import db
    from ..models import Student, Course, Enrollment
from forms import StudentForm
from flask_wtf import FlaskForm

students_bp = Blueprint('students', __name__)


@students_bp.route('/')
@login_required
def list():
    q = request.args.get('q', '')
    students = Student.query.filter(
        (Student.first_name.contains(q)) | (Student.last_name.contains(q))
    ).all()
    csrf_form = FlaskForm()
    return render_template('students/list.html', students=students, q=q, csrf_form=csrf_form)

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = StudentForm()
    if form.validate_on_submit():
        existing_student = Student.query.filter_by(email=form.email.data).first()
        if existing_student:
            flash('Email address already exists.', 'warning')
            return render_template('students/form.html', form=form, action="Add")
        student = Student(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data
        )
        try:
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding student: {e}', 'danger')
            return render_template('students/form.html', form=form, action="Add")
    return render_template('students/form.html', form=form, action="Add")


@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    if form.validate_on_submit():
        new_email = form.email.data
        if new_email != student.email:
            existing_student = Student.query.filter(Student.email == new_email, Student.id != id).first()
            if existing_student:
                flash('Email address already exists for another student.', 'warning')
                return render_template('students/form.html', form=form, student=student, action="Edit")

        form.populate_obj(student)
        try:
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating student: {e}', 'danger')
            return render_template('students/form.html', form=form, student=student, action="Edit")
    return render_template('students/form.html', form=form, student=student, action="Edit")


@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    csrf_form = FlaskForm()
    if not csrf_form.validate_on_submit():
         flash('Invalid CSRF token.', 'danger')
         return redirect(url_for('students.list'))

    student = Student.query.get_or_404(id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting student: {e}', 'danger')
    return redirect(url_for('students.list'))


@students_bp.route('/<int:id>')
@login_required
def detail(id):
    student = Student.query.get_or_404(id)
    all_courses = Course.query.order_by(Course.title).all()
    enrolled_course_ids = {enrollment.course_id for enrollment in student.enrollments}
    csrf_form = FlaskForm()

    return render_template(
        'students/detail.html',
        student=student,
        all_courses=all_courses,
        enrolled_course_ids=enrolled_course_ids,
        csrf_form=csrf_form
    )

@students_bp.route('/<int:student_id>/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_in_course(student_id, course_id):
    """Enrolls a student in a course and redirects back to the student detail page."""
    csrf_form = FlaskForm()

    if not csrf_form.validate_on_submit():
        flash('Invalid request or CSRF token expired.', 'danger')
        return redirect(url_for('students.detail', id=student_id))

    student = Student.query.get_or_404(student_id)
    course = Course.query.get_or_404(course_id)

    existing_enrollment = Enrollment.query.filter_by(
        student_id=student.id,
        course_id=course.id
    ).first()

    if existing_enrollment:
        flash(f'{student.first_name} is already enrolled in {course.title}.', 'warning')
    else:
        try:
            new_enrollment = Enrollment(student_id=student.id, course_id=course.id)
            db.session.add(new_enrollment)
            db.session.commit()
            flash(f'{student.first_name} successfully enrolled in {course.title}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error enrolling student: {e}', 'danger')

    return redirect(url_for('students.detail', id=student_id))
