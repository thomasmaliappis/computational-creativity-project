import os

import matplotlib.pyplot as plt
import torch
from PIL import Image
from flask import Flask, flash, request, redirect, url_for, render_template
from torchvision import transforms
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename

from fast_aging_gan.gan_module import Generator

import pixellib
from pixellib.tune_bg import alter_bg
import cv2

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['IMG_FOLDER'] = os.path.join('static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule(
    '/transform/<filename>?age=<age>&background=<background>', 'transform_file', build_only=True
)
app.add_url_rule(
    '/transform/<filename>?age=<age>', 'transform_file_without_background', build_only=True
)

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/transform': app.config['IMG_FOLDER']
})

# image_path = os.path.join(args.image_dir, filename)
model = Generator(ngf=32, n_residual_blocks=9)
ckpt = torch.load('./fast_aging_gan/pretrained_model/state_dict.pth', map_location='cpu')
model.load_state_dict(ckpt)
model.eval()
trans = transforms.Compose([
    transforms.Resize((1024, 1024)),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

change_bg = alter_bg()
change_bg.load_pascalvoc_model("deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def build_url(filename, age, background):
    if background != 'none':
        return redirect(url_for('transform_file', filename=filename, age=age, background=background))
    else:
        return redirect(url_for('transform_file_without_background', filename=filename, age=age))


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
    backgrounds = [
        {'background_name': 'none', 'background_id': 'none'},
        {'background_name': 'name1', 'background_id': 'id1'},
        {'background_name': 'name2', 'background_id': 'id2'}
    ]
    return render_template('upload.html', backgrounds=backgrounds)


@app.route('/transform/<filename>?', defaults={'age': None, 'background': None})
@app.route('/transform/<filename>?age=<age>', defaults={'background': None})
@app.route('/transform/<filename>?background=<background>', defaults={'age': None})
@app.route('/transform/<filename>?age=<age>&background=<background>')
@torch.no_grad()
def transformed_file(filename, age, background):
    # reading given image
    img_path = os.path.join(app.config['IMG_FOLDER'], filename)
    img = Image.open(img_path).convert('RGB')

    transformed_img_path = os.path.join(app.config['IMG_FOLDER'], 'transformed' + filename)
    # TODO
    #  replace with model function that generates transformed image
    #  use age and background as input parameters
    if age == 'yes':
        img = trans(img).unsqueeze(0)
        transformed_img = model(img)
        transformed_img = (transformed_img.squeeze().permute(1, 2, 0).numpy() + 1.0) / 2.0

        # saving transformed image
        plt.imsave(transformed_img_path, transformed_img)

    if background is not None:
        output = change_bg.change_bg_img(f_image_path=transformed_img_path,
                                         b_image_path="./static/orange-background.jpg",
                                         output_image_name=transformed_img_path)

    # select title and image to show
    if age == 'no' and background is None:
        title = 0
        img_path = '/' + img_path
    else:
        img_path = '/' + transformed_img_path
        title = 1 if age == 'yes' else 2
    return render_template('image.html', title=title, img_path=img_path)


if __name__ == '__main__':
    app.run()
