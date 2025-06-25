import re
import logging
import pandas as pd
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from rapidfuzz import process, fuzz
import easyocr

# ========== Config ==========
MODEL_NAME = "d4data/biomedical-ner-all"
DRUG_DB_PATH = r"G:\pharmaHub\Drug_DataBase.xlsx"
IMAGE_PATH = r"G:\pharmaHub\temp\your-image.jpg"  # replace as needed
FUZZY_THRESHOLD = 60

# ========== Setup ==========
logging.basicConfig(level=logging.INFO)
reader = easyocr.Reader(['en'])
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="max")

# ========== Load Dictionary ==========
def load_drug_list_from_excel(file_path):
    df = pd.read_excel(file_path)
    return df["name"].dropna().astype(str).tolist()

medical_dict = load_drug_list_from_excel(DRUG_DB_PATH)

# ========== OCR ==========
def ocr_image(file_path):
    result = reader.readtext(file_path, detail=0)
    return result

# ========== Preprocess ==========
def clean_text_lines(lines):
    return [
        line for line in lines
        if len(line) > 2 and re.search(r'[a-zA-Z]', line) and not re.search(r'https?://|\.(com|net|org)', line)
    ]

# ========== Fuzzy Correction ==========
def correct_text(lines, dictionary, threshold=FUZZY_THRESHOLD):
    corrected = []
    for line in lines:
        match, score, _ = process.extractOne(line.lower(), dictionary, scorer=fuzz.partial_ratio)
        if score >= threshold:
            corrected.append(match)
    return corrected

# ========== Extract Medical Entities ==========
def extract_medical_entities(text_list):
    text = " ".join(text_list)
    ents = ner_pipeline(text)
    results = [
        (ent['word'], ent['entity_group'], round(ent['score'], 2))
        for ent in ents if ent['score'] > 0.85
    ]
    return results

# ========== Main Pipeline ==========
def main(img_path):
    logging.info("Performing OCR...")
    raw_lines = ocr_image(img_path)
    logging.info(f"OCR lines: {raw_lines}")

    logging.info("Cleaning OCR lines...")
    cleaned_lines = clean_text_lines(raw_lines)
    logging.info(f"Cleaned lines: {cleaned_lines}")

    logging.info("Correcting with medical dictionary...")
    corrected = correct_text(cleaned_lines, medical_dict)
    logging.info(f"Corrected: {corrected}")

    logging.info("Extracting medical entities...")
    medical_entities = extract_medical_entities(corrected)
    logging.info(f"Extracted Entities: {medical_entities}")

    return {
        "ocr_lines": raw_lines,
        "corrected_text": corrected,
        "entities": medical_entities
    }

# ========== Run ==========
if __name__ == "__main__":
    result = main(IMAGE_PATH)
    print("\nFinal Output:")
    for k, v in result.items():
        print(f"{k}:\n{v}\n")
