# Author: Benony Gabriel
# Description: A Flask application for image steganography with encryption and decryption features.

from flask import Flask, render_template, request, redirect, send_file, flash, url_for, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import os
import io
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === UTILITY ===
def text_to_bin(text):
    return ''.join(format(ord(c), '08b') for c in text)

def bin_to_text(binary):
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join([chr(int(b, 2)) for b in chars])

def xor_encrypt_decrypt(message, key):
    key = (key * ((len(message) // len(key)) + 1))[:len(message)]
    return ''.join(chr(ord(m) ^ ord(k)) for m, k in zip(message, key))

# === ENKRIPSI ===
def encode_message(img, message):
    binary_msg = text_to_bin(message) + '1111111111111110'  # END MARKER
    pixels = list(img.getdata())
    encoded_pixels = []
    data_index = 0

    for pixel in pixels:
        r, g, b = pixel
        if data_index < len(binary_msg):
            r = (r & ~1) | int(binary_msg[data_index])
            data_index += 1
        if data_index < len(binary_msg):
            g = (g & ~1) | int(binary_msg[data_index])
            data_index += 1
        if data_index < len(binary_msg):
            b = (b & ~1) | int(binary_msg[data_index])
            data_index += 1
        encoded_pixels.append((r, g, b))

    img.putdata(encoded_pixels)
    return img

# === DEKRIPSI ===
def decode_message(img):
    pixels = list(img.getdata())
    binary_data = ''
    for pixel in pixels:
        for color in pixel[:3]:
            binary_data += str(color & 1)

    end_marker = '1111111111111110'
    end_index = binary_data.find(end_marker)
    if end_index == -1:
        return None

    return bin_to_text(binary_data[:end_index])

# === ROUTES ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    if request.method == 'POST':
        image = request.files.get('image')
        message = request.form.get('message')
        key = request.form.get('key')

        if not image or not message or not key:
            flash('Semua input wajib diisi!', 'error')
            return redirect(request.url)

        if not image.filename.lower().endswith('.png'):
            flash('File harus berformat .png', 'error')
            return redirect(request.url)

        img = Image.open(image)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        encrypted_message = xor_encrypt_decrypt(message, key)
        encoded_img = encode_message(img, encrypted_message)

        # filename = 'encoded.png'
        # output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # encoded_img.save(output_path)

        img_io = BytesIO()
        encoded_img.save(img_io, 'PNG')
        img_io.seek(0)

        flash('Pesan berhasil disisipkan ke gambar! Klik tombol unduh untuk menyimpan.', 'success')
        # return redirect(url_for('encrypt', filename=filename))
        return send_file(img_io, mimetype='image/png')

    # filename = request.args.get('filename')
    # return render_template('encrypt.html', filename=filename)
    return render_template('encrypt.html')


@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    if request.method == 'POST':
        image = request.files.get('image')
        key = request.form.get('key')

        if not image or not key:
            flash('Gambar dan kunci wajib diisi!', 'error')
            return redirect(request.url)

        if not image.filename.lower().endswith('.png'):
            flash('File harus berformat .png', 'error')
            return redirect(request.url)

        img = Image.open(image)
        encrypted_message = decode_message(img)

        if encrypted_message is None:
            flash('Tidak ditemukan pesan rahasia!', 'error')
            return redirect(request.url)

        decrypted_message = xor_encrypt_decrypt(encrypted_message, key)
        return render_template('decrypt.html', result=decrypted_message)

    return render_template('decrypt.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

# # === API ENDPOINTS Utk Versi Mobile App ===
# @app.route('/api/encrypt', methods=['POST'])
# def api_encrypt():
#     if 'image' not in request.files or 'message' not in request.form or 'key' not in request.form:
#         return jsonify({'error': 'Missing required fields'}), 400

#     image = request.files['image']
#     message = request.form['message']
#     key = request.form['key']

#     if not image.filename.lower().endswith('.png'):
#         return jsonify({'error': 'File must be PNG'}), 400

#     try:
#         img = Image.open(image)
#         if img.mode != 'RGB':
#             img = img.convert('RGB')

#         encrypted_message = xor_encrypt_decrypt(message, key)
#         encoded_img = encode_message(img, encrypted_message)

#         # Simpan file sementara
#         output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'api_encoded.png')
#         encoded_img.save(output_path)

#         return send_file(output_path, mimetype='image/png')
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/decrypt', methods=['POST'])
# def api_decrypt():
#     if 'image' not in request.files or 'key' not in request.form:
#         return jsonify({'error': 'Missing required fields'}), 400

#     image = request.files['image']
#     key = request.form['key']

#     if not image.filename.lower().endswith('.png'):
#         return jsonify({'error': 'File must be PNG'}), 400

#     try:
#         img = Image.open(image)
#         if img.mode != 'RGB':
#             img = img.convert('RGB')

#         encrypted_message = decode_message(img)
#         if encrypted_message is None:
#             return jsonify({'error': 'No hidden message found'}), 404

#         decrypted_message = xor_encrypt_decrypt(encrypted_message, key)
#         return jsonify({'message': decrypted_message})
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# # ===========================END OF FILE===========================


if __name__ == '__main__':
    app.run(debug=True)
