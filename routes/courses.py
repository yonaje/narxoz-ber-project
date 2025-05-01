import os
from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm 

from extensions import db
from models import Course, Student, Enrollment
from forms import CourseForm

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/')
@login_required
def list():
    courses = Course.query.order_by(Course.start_date.desc()).all()
    csrf_form = FlaskForm()
    return render_template('courses/list.html', courses=courses, csrf_form=csrf_form)

@courses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = CourseForm()
    if form.validate_on_submit():
        new_course = Course(
            title=form.title.data,
            start_date=form.start_date.data,
            user_id=current_user.id
        )
        file = form.material.data
        if file:
            filename = secure_filename(file.filename)
            allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'txt', 'pdf', 'mp3', 'mp4'})
            upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER']) 
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                new_course.material_path = filename
                save_path = os.path.join(upload_folder_abs, filename)
                try:
                    os.makedirs(upload_folder_abs, exist_ok=True)
                    file.save(save_path)
                    flash(f'Material "{filename}" uploaded successfully.', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error saving file: {e}', 'danger')
                    return render_template('courses/form.html', form=form, action="Add")
            else:
                flash(f'File type not allowed for "{filename}". Allowed: {", ".join(allowed_extensions)}', 'warning')
                return render_template('courses/form.html', form=form, action="Add")

        try:
            db.session.add(new_course)
            db.session.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('courses.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding course to database: {e}', 'danger')
            return render_template('courses/form.html', form=form, action="Add")

    return render_template('courses/form.html', form=form, action="Add")


@courses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    course = Course.query.get_or_404(id)
    form = CourseForm(obj=course)

    if request.method == 'POST':
        pass 
    if form.validate_on_submit():
        course.title = form.title.data
        course.start_date = form.start_date.data
        if not course.user_id:
             course.user_id = current_user.id

        file = form.material.data
        if file:
            filename = secure_filename(file.filename)
            allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'txt', 'pdf', 'mp3', 'mp4'})
            upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])

            if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                if course.material_path and course.material_path != filename:
                    old_file_path = os.path.join(upload_folder_abs, course.material_path)
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                            flash(f'Old material "{course.material_path}" removed.', 'info')
                        except OSError as e:
                            flash(f'Error removing old file: {e}', 'warning')
                course.material_path = filename
                save_path = os.path.join(upload_folder_abs, filename)
                try:
                    os.makedirs(upload_folder_abs, exist_ok=True)
                    file.save(save_path)
                    flash(f'New material "{filename}" uploaded.', 'success')
                except Exception as e:
                    flash(f'Error saving new file: {e}', 'danger')
                    current_material = course.material_path
                    return render_template('courses/form.html', form=form, course=course, action="Edit", current_material=current_material)
            else:
                 flash(f'File type not allowed for "{filename}". Allowed: {", ".join(allowed_extensions)}', 'warning')
                 current_material = course.material_path
                 return render_template('courses/form.html', form=form, course=course, action="Edit", current_material=current_material)
        try:
            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('courses.list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating course: {e}', 'danger')
            current_material = course.material_path
            return render_template('courses/form.html', form=form, course=course, action="Edit", current_material=current_material)

    current_material = course.material_path
    if request.method == 'GET':
        form.title.data = course.title
        form.start_date.data = course.start_date

    return render_template('courses/form.html', form=form, course=course, action="Edit", current_material=current_material)



@courses_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    csrf_form = FlaskForm()
    if not csrf_form.validate_on_submit():
         flash('Invalid CSRF token.', 'danger')
         return redirect(url_for('courses.list'))

    course = Course.query.get_or_404(id)

    if course.material_path:
        upload_folder_abs = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'])
        file_path = os.path.join(upload_folder_abs, course.material_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                flash(f'Material file "{course.material_path}" deleted.', 'info')
            except OSError as e:
                flash(f'Error deleting file: {e}', 'warning')

    try:
        db.session.delete(course)
        db.session.commit()
        flash('Course record and associated enrollments deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting course record: {e}', 'danger')

    return redirect(url_for('courses.list'))


@courses_bp.route('/<int:id>')
@login_required
def detail(id):
    course = Course.query.get_or_404(id)
    all_students = Student.query.order_by(Student.last_name, Student.first_name).all()
    enrolled_student_ids = {enrollment.student_id for enrollment in course.enrollments}
    csrf_form = FlaskForm()

    return render_template(
        'courses/detail.html',
        course=course,
        all_students=all_students,
        enrolled_student_ids=enrolled_student_ids,
        csrf_form=csrf_form 
    )


@courses_bp.route('/<int:course_id>/add_student/<int:student_id>', methods=['POST'])
@login_required
def add_student_enrollment(course_id, student_id):
    csrf_form = FlaskForm()
    if not csrf_form.validate_on_submit():
        flash('Invalid request or CSRF token expired.', 'danger')
        return redirect(url_for('courses.detail', id=course_id))

    course = Course.query.get_or_404(course_id)
    student = Student.query.get_or_404(student_id)

    existing_enrollment = Enrollment.query.filter_by(course_id=course.id, student_id=student.id).first()
    if existing_enrollment:
        flash(f'{student.first_name} {student.last_name} is already enrolled in {course.title}.', 'warning')
    else:
        try:
            new_enrollment = Enrollment(course_id=course.id, student_id=student.id)
            db.session.add(new_enrollment)
            db.session.commit()
            flash(f'{student.first_name} {student.last_name} successfully enrolled in {course.title}.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error enrolling student: {e}', 'danger')

    return redirect(url_for('courses.detail', id=course_id))

@courses_bp.route('/<int:course_id>/unenroll/<int:student_id>', methods=['POST'])
@login_required
def remove_student_enrollment(course_id, student_id):
    """Removes a student's enrollment from a course."""
    csrf_form = FlaskForm()
    if not csrf_form.validate_on_submit():
        flash('Invalid request or CSRF token expired.', 'danger')
        return redirect(url_for('courses.detail', id=course_id))

    enrollment = Enrollment.query.filter_by(
        course_id=course_id,
        student_id=student_id
    ).first() 

    if not enrollment:
        flash('Enrollment record not found. Perhaps the student was already unenrolled.', 'warning')
        return redirect(url_for('courses.detail', id=course_id))

    student_name = f"{enrollment.student.first_name} {enrollment.student.last_name}"
    course_title = enrollment.course.title

    try:
        db.session.delete(enrollment)
        db.session.commit()
        flash(f'{student_name} successfully unenrolled from {course_title}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error unenrolling student: {e}', 'danger')

    return redirect(url_for('courses.detail', id=course_id))