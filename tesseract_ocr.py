import logging

import pytesseract
from PIL import Image


def get_text_from_image_with_tesseract(image_path):
    try:
        # Abre a imagem com PIL
        img = Image.open(image_path)
        # Usa Tesseract para fazer OCR
        text = pytesseract.image_to_string(img, lang='por')  # 'por' para português
        logging.info(f"Texto extraído da imagem: {text}")
        return text
    except Exception as e:
        print(f"Erro ao processar a imagem com Tesseract: {e}")
        return ""
