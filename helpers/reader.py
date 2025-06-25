import pandas as pd

from docx import Document
from pytesseract import image_to_string
from PyPDF2 import PdfReader


def image(image_path):
    from PIL import Image
    image = Image.open(image_path)
    return image_to_string(image, "eng")

def pdf(pdf_path):
    reader = PdfReader(pdf_path)
    return "\n".join([page.extract_text() for page in reader.pages])

def excel(excel_path):
    df = pd.read_excel(excel_path)
    return df.to_string(index=False)

def word(word_path):
    doc = Document(word_path)
    context = ""
    for paragraph in doc.paragraphs:
        context = context + paragraph.text + "\n"
    print(context)
    return context