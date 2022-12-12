import os
from PIL import Image
from flask import Flask, flash, request, redirect, url_for, send_from_directory, render_template
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware

IMG_FOLDER = './images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['IMG_FOLDER'] = IMG_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule(
    '/transform/<filename>?age=<age>&background=<background>', 'transform_file', build_only=True
)
app.add_url_rule(
    '/transform/<filename>?age=<age>', 'transform_file_without_background', build_only=True
)
app.add_url_rule(
    '/transform/<filename>?background=<background>', 'transform_file_without_age', build_only=True
)
app.add_url_rule(
    '/transform/<filename>?', 'transform_file_without_age_and_background', build_only=True
)

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/transform': app.config['IMG_FOLDER']
})


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def build_url(filename, age, background):
    if age != 'none' and background != 'none':
        return redirect(url_for('transform_file', filename=filename, age=age, background=background))
    elif age == 'none' and background != 'none':
        return redirect(url_for('transform_file_without_age', filename=filename, background=background))
    elif age != 'none' and background == 'none':
        return redirect(url_for('transform_file_without_background', filename=filename, age=age))
    elif age == 'none' and background == 'none':
        return redirect(url_for('transform_file_without_age_and_background', filename=filename))


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
            file.save(os.path.join(app.config['IMG_FOLDER'], filename))
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


@app.route('/transform/<filename>?', defaults={'age': None, 'background': None})
@app.route('/transform/<filename>?age=<age>', defaults={'background': None})
@app.route('/transform/<filename>?background=<background>', defaults={'age': None})
@app.route('/transform/<filename>?age=<age>&background=<background>')
def transformed_file(filename, age, background):
    # reading given image
    img_path = app.config['IMG_FOLDER'] + '/' + filename
    img = Image.open(img_path)

    # TODO
    #  replace with model function that generates transformed image
    #  use age and background as input parameters
    transformed_img = img

    # saving transformed image
    transformed_img_path = app.config['IMG_FOLDER'] + '/transformed' + filename
    transformed_img.save(transformed_img_path)

    # show transformed image
    return send_from_directory(app.config['IMG_FOLDER'], 'transformed' + filename)
    # TODO
    #  create page to show transformed image
    # return render_template('transformed.html', image=transformed_img_path)


@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)


if __name__ == '__main__':
    app.run()
