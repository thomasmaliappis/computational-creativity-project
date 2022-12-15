import os

import cv2
import matplotlib.pyplot as plt
import torch
from PIL import Image
from flask import Flask, flash, request, redirect, url_for, render_template
from pixellib.tune_bg import alter_bg
from torchvision import transforms
from torchvision.transforms.functional import to_pil_image
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.utils import secure_filename

from anime_gan.model import Generator as anime_Generator
from fast_aging_gan.gan_module import Generator as age_Generator

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['IMG_FOLDER'] = os.path.join('static', 'images')
app.config['BG_FOLDER'] = os.path.join('static', 'backgrounds')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule(
    '/transform/<filename>?age=<age>&anime=<anime>&sketch=<sketch>&background=<background>', 'transform_file',
    build_only=True
)

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/transform': app.config['IMG_FOLDER']
})

# age model
age_model = age_Generator(ngf=32, n_residual_blocks=9)
age_model.load_state_dict(torch.load('./fast_aging_gan/pretrained_model/state_dict.pth', map_location='cpu'))
age_model.eval()
trans = transforms.Compose([
    transforms.Resize((512, 512)),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

# anime model
anime_model = anime_Generator()
anime_model.load_state_dict(torch.load('./anime_gan/weights/paprika.pt', map_location="cpu"))
anime_model.eval()

change_bg = alter_bg()
change_bg.load_pascalvoc_model("deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")


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
            file.save(os.path.join(app.config['IMG_FOLDER'], filename))
            background = request.form['background']
            return redirect(
                url_for('transform_file',
                        filename=filename, age=request.form['age'], anime=request.form['anime'],
                        sketch=request.form['sketch'], background=background))
    backgrounds = [{'background_name': 'none', 'background_id': 'none'}] + [
        {'background_name': file.replace('.jpg', ''), 'background_id': file.replace('.jpg', '')} for file in
        os.listdir('./static/backgrounds')]
    return render_template('upload.html', backgrounds=backgrounds)


@app.route('/transform/<filename>?age=<age>&anime=<anime>&sketch=<sketch>&background=<background>')
@torch.no_grad()
def transformed_file(filename, age, anime, sketch, background):
    # reading given image
    img_path = os.path.join(app.config['IMG_FOLDER'], filename)
    age = True if age == 'yes' else False
    anime = True if anime == 'yes' else False
    sketch = True if sketch == 'yes' else False

    if age:
        img = Image.open(img_path).convert('RGB')
        img = trans(img).unsqueeze(0)
        transformed_img = age_model(img)
        transformed_img = (transformed_img.squeeze().permute(1, 2, 0).numpy() + 1.0) / 2.0

        # saving transformed image
        filename = 'age_' + filename
        aged_img_path = os.path.join(app.config['IMG_FOLDER'], filename)
        plt.imsave(aged_img_path, transformed_img)
        img_path = aged_img_path

    if background != 'none':
        background_path = os.path.join(app.config['BG_FOLDER'], background + '.jpg')
        filename = 'bg_' + filename
        changed_bg_img_path = os.path.join(app.config['IMG_FOLDER'], filename)
        change_bg.change_bg_img(f_image_path=img_path, b_image_path=background_path,
                                output_image_name=changed_bg_img_path)
        img_path = changed_bg_img_path

    if anime:
        filename = 'anime_' + filename
        anime_img_path = os.path.join(app.config['IMG_FOLDER'], filename)
        img = Image.open(img_path).convert("RGB")
        with torch.no_grad():
            image = trans(img).unsqueeze(0) * 2 - 1
            out = anime_model(image.to('cpu'), False).cpu()
            out = out.squeeze(0).clip(-1, 1) * 0.5 + 0.5
            out = to_pil_image(out)

        out.save(anime_img_path)
        img_path = anime_img_path

    if sketch:
        img = cv2.imread(img_path)  # loads an image from the specified file
        # convert an image from one color space to another
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        invert = cv2.bitwise_not(grey_img)  # helps in masking of the image
        # sharp edges in images are smoothed while minimizing too much blurring
        blur = cv2.GaussianBlur(invert, (21, 21), 0)
        invertedblur = cv2.bitwise_not(blur)
        sketch = cv2.divide(grey_img, invertedblur, scale=256.0)
        filename = 'sketch_' + filename
        sketched_img_path = os.path.join(app.config['IMG_FOLDER'], filename)
        cv2.imwrite(sketched_img_path, sketch)  # converted image is saved as mentioned name
        img_path = sketched_img_path

    img_path = '/' + img_path
    # TODO Change titles
    title = 'Result'
    return render_template('image.html', title=title, img_path=img_path)


if __name__ == '__main__':
    app.run()
