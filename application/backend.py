"""Framework for grading student submissions."""

import os
import openai
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SubmitField, FileField
from wtforms.validators import DataRequired
from wtforms.widgets import FileInput
from werkzeug.utils import secure_filename


UPLOAD_FOLDER = 'uploads'

app = Flask(__name__, static_folder="./static")
app.config['SECRET_KEY'] = open("../__secrets/flask", "r").read()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap(app)

openai.api_key = open("../__secrets/openai", "r").read()


class Multifile(FileInput):
    """Handles multiple file uploads."""
    input_type = 'file'

    def __call__(self, field, **kwargs):
        """Override the default behavior to allow multiple files."""
        kwargs.setdefault('multiple', True)
        return super(Multifile, self).__call__(field, **kwargs)


class GradingForm(FlaskForm):
    """Form for inputting the assignment description and uploading submissions."""
    description = TextAreaField('Assignment description:',
                                validators=[DataRequired()], render_kw={"rows": 8})
    focus = StringField('Main focus:')
    submissions = FileField('Submissions to grade',
                            validators=[DataRequired()], widget=Multifile())
    grade = SubmitField('Grade')


@app.route('/', methods=['GET', 'POST'])
def assignment():
    """Route for uploading the assignment description and student submissions."""
    task = GradingForm()

    if task.validate_on_submit():
        session['assignment'] = task.description.data
        session['focus'] = task.focus.data

        # Remove old files from disk.
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))

        # Save new files to disk.
        for file in request.files.getlist('submissions'):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        return redirect(url_for('grade'))
    return render_template('assignment.html', task=task)


@app.route('/grade', methods=['GET', 'POST'])
def grade():
    files = sorted(os.listdir(app.config['UPLOAD_FOLDER']))

    if not files:
        return redirect(url_for('assignment'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == "next" and session['index'] < len(files) - 1:
            session['index'] += 1
        elif action == "prev" and session['index'] > 0:
            session['index'] -= 1

        return redirect(url_for('grade'))

    file = files[session['index']]
    path = os.path.join(app.config['UPLOAD_FOLDER'], file)

    with open(path, 'r') as f:
        code = f.read()

    feedback = gpt(session['assignment'], session['focus'], code)

    return render_template('grade.html',
                           filename=file, code=code, total=len(files),
                           feedback=feedback)


def gpt(task, focus, code):
    prompt = (f"Evaluate the following student submission based on the task: \n\n"
              f"{task} \n\n"
              f"where the main focus is: \n\n"
              f"{focus}. \n\n"
              f"Evaluate their code and assess whether they have satisfied the task and main "
              f"focus of the exercies based on their submission:"
              f"\n\n---\n\n {code} \n\n---\n\n"
              f"Feedback:")
    # response = openai.Completion.create(engine="davinci", prompt=prompt, max_tokens=150)
    # feedback = response.choices[0].text.strip()
    feedback = "This is a test feedback"

    return feedback


if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
