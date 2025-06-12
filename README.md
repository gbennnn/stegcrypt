# stegcrypt

StegCrypt is a lightweight steganography tool for securely embedding and extracting hidden messages within digital images.

## Features

- Hide (embed) secret text messages into digital images
- Extract hidden messages from previously encoded images
- Lightweight and easy to use
- Built with Python and Flask
- Web-based interface: [Try it live](https://stegcrypt.onrender.com)
- Open-source under the MIT License

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/gbennnn/stegcrypt.git
   cd stegcrypt
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```
   The app will be available at `http://127.0.0.1:5000/`

### Usage

1. Open the web interface.
2. To embed a message:
   - Upload a cover image (PNG).
   - Enter your secret message.
   - Enter your secret key (for encoding).
   - Click "Encode" to download the stego-image.
3. To extract a message:
   - Upload a stego-image encoded with stegcrypt.
   - Enter your secret key (for decoding).
   - Click "Decode" to reveal the hidden message.

## Technologies Used

- Python
- Flask
- HTML & Tailwind CSS
- Pillow (PIL) for image processing

## License

This project is licensed under the [MIT License](LICENSE).

## Links

- [Live Demo](https://stegcrypt.onrender.com)
- [GitHub Repository](https://github.com/gbennnn/stegcrypt)

---

> StegCrypt is intended for educational and legitimate privacy use only. Do not use it for illegal purposes.
