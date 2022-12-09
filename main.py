import os
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware

UPLOAD_FOLDER = './images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule(
    '/uploads/<filename>?age=<age>&background=<background>', 'uploaded_file', build_only=True
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
            return redirect(url_for('uploaded_file', filename=filename, age=age,background=background))
    backgrounds = [
        {'background_name': 'name1', 'background_id': 'id1'},
        {'background_name': 'name2', 'background_id': 'id2'}
    ]
    return render_template('upload.html', backgrounds=backgrounds)


@app.route('/uploads/<filename>?age=<age>&background=<background>')
def uploaded_file(filename, age, background):
    # TODO

    # if age is specified
    # call model and transform original image according to age value
    # if background
    # is specified change background of image
    # redirect to new image
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
