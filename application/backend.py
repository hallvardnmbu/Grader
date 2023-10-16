"""Framework for grading student submissions."""

import os
import openai
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SubmitField, FileField
from wtforms.validators import DataRequired
from wtforms.widgets import FileInput


UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['SECRET_KEY'] = open("../__secrets/flask", "r").read()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap(app)

openai.api_key = open("../__secrets/openai", "r").read()


class TaskInputForm(FlaskForm):
    task_description = TextAreaField('Task Description', validators=[DataRequired()])
    key_points = StringField('Key Points (comma-separated)', validators=[DataRequired()])
    submit = SubmitField('Next')


class MultiFileInput(FileInput):
    input_type = 'file'

    def __call__(self, field, **kwargs):
        kwargs.setdefault('multiple', True)
        return super(MultiFileInput, self).__call__(field, **kwargs)


class UploadForm(FlaskForm):
    submissions = FileField('Upload Student Submissions', validators=[DataRequired()], widget=MultiFileInput())
    upload = SubmitField('Upload & Grade')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TaskInputForm()
    if form.validate_on_submit():
        session['task_description'] = form.task_description.data
        session['key_points'] = form.key_points.data.split(',')
        return redirect(url_for('upload'))
    return render_template('task.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        uploaded_files = request.files.getlist('submissions')
        for file in uploaded_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
        session['uploaded_files'] = [file.filename for file in uploaded_files]
        session['current_index'] = 0
        return redirect(url_for('grade'))
    return render_template('upload.html', form=form)


@app.route('/grade', methods=['GET', 'POST'])
def grade():
    if 'uploaded_files' not in session or session['current_index'] >= len(session['uploaded_files']):
        return redirect(url_for('index'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == "next":
            session['current_index'] += 1
        elif action == "prev" and session['current_index'] > 0:
            session['current_index'] -= 1
        return redirect(url_for('grade'))

    current_file = session['uploaded_files'][session['current_index']]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], current_file)

    with open(file_path, 'r') as f:
        code = f.read()

    feedback, improvement_points = grade_gpt(session['task_description'], session['key_points'], code)

    return render_template('grade.html', filename=current_file, code=code, feedback=feedback, improvements=improvement_points, total_submissions=len(session['uploaded_files']))


def grade_gpt(task_description, key_points, student_code):
    prompt = f"Evaluate the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nFeedback: "
    response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=150)
    feedback = response.choices[0].text.strip()

    improvement_prompt = f"Suggest improvements for the following student submission based on the task: '{task_description}' and key points: {', '.join(key_points)}.\n\n---\n\n{student_code}\n\n---\n\nImprovements: "
    improvement_response = openai.Completion.create(engine="davinci", prompt=improvement_prompt, max_tokens=150)
    improvement_points = improvement_response.choices[0].text.strip()

    return feedback, improvement_points


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
