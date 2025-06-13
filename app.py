from flask import Flask, render_template, request, redirect, send_file, flash, url_for
from werkzeug.utils import secure_filename
from PIL import Image
import os
import io
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === UTILITY ===
def text_to_bin(text):
    """Mengubah teks menjadi representasi biner."""
    return ''.join(format(ord(c), '08b') for c in text)

def bin_to_text(binary):
    """Mengubah representasi biner kembali menjadi teks."""
    # Memastikan panjang biner adalah kelipatan 8
    if len(binary) % 8 != 0:
        binary = binary[:-(len(binary) % 8)]
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join([chr(int(b, 2)) for b in chars])

def aes_encrypt(message, key):
    """Mengenkripsi pesan menggunakan AES."""
    key = key.encode('utf-8')
    key = key[:16].ljust(16, b'\0')  # Memastikan kunci adalah 16 byte untuk AES-128
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(message.encode('utf-8'), AES.block_size))
    # Menggabungkan IV dengan ciphertext untuk dekripsi
    return base64.b64encode(cipher.iv + ct_bytes).decode('utf-8')

def aes_decrypt(ciphertext, key):
    """Mendekripsi pesan menggunakan AES."""
    key = key.encode('utf-8')
    key = key[:16].ljust(16, b'\0')  # Memastikan kunci adalah 16 byte untuk AES-128
    data = base64.b64decode(ciphertext)
    iv = data[:16] # Ekstrak IV dari awal data
    ct = data[16:] # Sisanya adalah ciphertext
    cipher = AES.new(key, AES.MODE_CBC, iv)
    # Mendekripsi dan menghapus padding
    return unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')

# === ENKRIPSI STEGANOGRAFI ===
def encode_message(img, message):
    """Menyisipkan pesan biner ke dalam piksel gambar."""
    binary_msg = text_to_bin(message) + '1111111111111110'  # Penanda akhir pesan
    pixels = list(img.getdata())
    
    # Periksa apakah gambar memiliki kapasitas yang cukup
    if len(binary_msg) > len(pixels) * 3:
        return None # Pesan terlalu besar

    encoded_pixels = []
    data_index = 0

    for pixel in pixels:
        r, g, b = pixel
        # Ubah LSB (Least Significant Bit) dari setiap komponen warna
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

    # Buat gambar baru dengan piksel yang sudah dimodifikasi
    img.putdata(encoded_pixels)
    return img

# === DEKRIPSI STEGANOGRAFI ===
def decode_message(img):
    """Mengekstrak pesan biner dari piksel gambar."""
    pixels = list(img.getdata())
    binary_data = ''
    for pixel in pixels:
        # Ekstrak LSB dari komponen R, G, B
        for color in pixel[:3]:
            binary_data += str(color & 1)

    end_marker = '1111111111111110'
    end_index = binary_data.find(end_marker)
    if end_index == -1:
        return None # Penanda akhir tidak ditemukan

    return bin_to_text(binary_data[:end_index])

# === ROUTES ===
@app.route('/')
def index():
    """Menampilkan halaman utama."""
    return render_template('index.html')

@app.route('/encrypt', methods=['GET', 'POST'])
def encrypt():
    """Menangani proses enkripsi."""
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
        
        # PERBAIKAN: Konversi gambar ke mode 'RGB' untuk konsistensi
        img = Image.open(image).convert('RGB')
        
        # Enkripsi pesan sebelum disisipkan
        encrypted_message = aes_encrypt(message, key)
        
        # Salin gambar untuk dimodifikasi
        encoded_img = encode_message(img.copy(), encrypted_message)

        # PERBAIKAN: Tangani jika pesan terlalu besar untuk gambar
        if encoded_img is None:
            flash('Pesan terlalu panjang untuk disisipkan pada gambar ini.', 'error')
            return redirect(request.url)

        # Simpan gambar yang sudah dimodifikasi
        filename = 'encoded.png'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        encoded_img.save(output_path)

        flash('Pesan berhasil disisipkan!', 'success')
        return render_template('encrypt.html', filename=filename)

    return render_template('encrypt.html')

@app.route('/download/<filename>')
def download_file(filename):
    """Menyediakan file untuk diunduh."""
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/decrypt', methods=['GET', 'POST'])
def decrypt():
    """Menangani proses dekripsi."""
    if request.method == 'POST':
        image = request.files.get('image')
        key = request.form.get('key')

        if not image or not key:
            flash('Gambar dan kunci wajib diisi!', 'error')
            return redirect(request.url)

        if not image.filename.lower().endswith('.png'):
            flash('File harus berformat .png', 'error')
            return redirect(request.url)
        
        # PERBAIKAN: Konversi gambar ke mode 'RGB' untuk konsistensi
        img = Image.open(image).convert('RGB')
        
        # Ekstrak pesan terenkripsi dari gambar
        encrypted_message = decode_message(img)

        if encrypted_message is None:
            flash('Tidak ditemukan pesan rahasia!', 'error')
            return redirect(request.url)

        try:
            # Dekripsi pesan
            decrypted_message = aes_decrypt(encrypted_message, key)
        except Exception:
            flash('Gagal mendekripsi pesan. Cek kembali kunci Anda!', 'error')
            return redirect(request.url)

        return render_template('decrypt.html', result=decrypted_message)

    return render_template('decrypt.html')

if __name__ == '__main__':
    app.run(debug=True)
