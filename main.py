import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware

UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule(
    '/uploads/<filename>?age=<age>&background=<background>', 'upload_file', build_only=True
)
app.add_url_rule(
    '/uploads/<filename>?age=<age>', 'upload_file_without_background', build_only=True
)
app.add_url_rule(
    '/uploads/<filename>?background=<background>', 'upload_file_without_age', build_only=True
)
app.add_url_rule(
    '/uploads/<filename>', 'upload_file_without_age_and_background', build_only=True
)
app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/uploads': app.config['UPLOAD_FOLDER']
})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def build_url(filename, age, background):
    if age and background != 'none':
        return redirect(url_for('upload_file', filename=filename, age=age, background=background))
    elif age and background != 'none':
        return redirect(url_for('upload_file_without_age', filename=filename, background=background))
    elif not age and background == 'none':
        return redirect(url_for('upload_file_without_background', filename=filename, age=age))
    elif not age and background == 'none':
        return redirect(url_for('upload_file_without_age_and_background', filename=filename))


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            age = request.form['age']
            background = request.form['background']
            return build_url(filename, age, background)
    ages = [
        {'age_name': 'none', 'age_id': 'none'},
        {'age_name': '10', 'age_id': '10'},
        {'age_name': '50', 'age_id': '50'}
    ]
    backgrounds = [
        {'background_name': 'none', 'background_id': 'none'},
        {'background_name': 'name1', 'background_id': 'id1'},
        {'background_name': 'name2', 'background_id': 'id2'}
    ]
    return render_template('upload.html', ages=ages, backgrounds=backgrounds)


@app.route('/uploads/<filename>', defaults={'age': None, 'background': None})
@app.route('/uploads/<filename>?age=<age>', defaults={'background': None})
@app.route('/uploads/<filename>?background=<background>', defaults={'age': None})
@app.route('/uploads/<filename>?age=<age>&background=<background>')
def uploaded_file(filename, age, background):
    # TODO
    # if age is specified
    # call model and transform original image according to age value
    # if background
    # is specified change background of image
    # redirect to new image
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)


if __name__ == '__main__':
    app.run()
