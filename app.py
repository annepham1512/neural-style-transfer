from flask import Flask, render_template, request, send_file
from PIL import Image
from io import BytesIO
import numpy as np
import PIL.Image
import tensorflow as tf
import tensorflow_hub as hub
import os

os.environ['TFHUB_MODEL_LOAD_FORMAT'] = 'COMPRESSED'
hub_model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')

app = Flask(__name__)

def load_img(img):
    max_dim = 512
    img = tf.image.decode_image(img.getvalue(), channels=3)
    img = tf.image.convert_image_dtype(img, tf.float32)
    shape = tf.cast(tf.shape(img)[:-1], tf.float32)
    long_dim = max(shape)
    scale = max_dim / long_dim

    new_shape = tf.cast(shape * scale, tf.int32)

    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]
    return img

def tensor_to_image(tensor):
    tensor = tensor*255
    tensor = np.array(tensor, dtype=np.uint8)
    if np.ndim(tensor)>3:
        assert tensor.shape[0] == 1
        tensor = tensor[0]
    return PIL.Image.fromarray(tensor)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge-images', methods=['POST'])
def merge_images():
    # Get the images from the request
    content_image = request.files['image1']
    style_image = request.files['image2']
    
    # Open images using PIL
    # content_image = Image.open(image1)
    # style_image = Image.open(image2)

    content_image = load_img(content_image)
    style_image = load_img(style_image)

    stylized_image = hub_model(tf.constant(content_image), tf.constant(style_image))[0]
    stylized_image = tensor_to_image(stylized_image)

    # Save the combined image to a BytesIO object
    img_byte_arr = BytesIO()
    stylized_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return send_file(img_byte_arr, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=False)
