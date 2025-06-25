import logging
import pandas as pd
from rapidfuzz import process, fuzz
from PIL import Image
import google.generativeai as genai
import os
import re

genai.configure(api_key='AIzaSyD2ocIaSbrcep_fThJSREmAQVqmiO_NxGk')

# ========== Config ==========
DRUG_DB_PATH = r"G:\pharmaHubGP\pharmaHubAI\Drug_DataBase.xlsx"
IMAGE_PATH = r"G:\pharmaHubGP\pharmaHubAI\temp\%D8%B1%D9%88%D8%B4%D8%AA%D8%A9-%D8%A7%D9%84%D8%AA%D9%87%D8%A7%D8%A8-%D8%A7%D9%84%D8%A8%D8%B1%D9%88%D8%B3%D8%AA%D8%A7%D8%AA%D8%A7-%D9%81%D9%84%D9%88%D8%A8%D8%A7%D8%AF%D9%83%D8%B3-%D8%AA%D8%A7%D9%81%D8%A7%D8%B3%D9%8A%D9%86.jpg"  # replace as needed
FUZZY_THRESHOLD = 83

# ========== Setup ==========
logging.basicConfig(level=logging.INFO)

def load_drug_list_from_excel(file_path):
    df = pd.read_excel(file_path)
    return df["name"].dropna().astype(str).tolist()

medical_dict = load_drug_list_from_excel(DRUG_DB_PATH)

def ocr_image_with_gemini(file_path):
    from PIL import Image
    model = genai.GenerativeModel("gemini-1.5-flash")
    image = Image.open(file_path)

    prompt = (
        "You are a medical OCR expert. Extract all readable medicine names, dosages, and medical instructions "
        "from this image of a handwritten prescription. Output the result as a list of text lines, exactly as they appear, "
        "preserving the order. Skip irrelevant parts like logos, emails, or URLs,"
        "Your response should only contain a list of text lines without any additional commentary,"
        "and ensure that each line is meaningful and relevant to the prescription and don't include the R symbol."
    )

    response = model.generate_content([prompt, image])

    text = response.text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return lines


# ========== Preprocess ==========
def clean_text_lines(lines):
    return [
        line for line in lines
        if len(line) > 2 and re.search(r'[a-zA-Z]', line) and not re.search(r'https?://|\.(com|net|org)', line)
    ]

def correct_text(lines, dictionary, threshold=FUZZY_THRESHOLD):
    corrected = []
    for line in lines:
        match, score, _ = process.extractOne(line.lower(), dictionary, scorer=fuzz.partial_ratio)
        if score >= threshold:
            corrected.append(match)
    return corrected

# # ========== Extract Medical Entities ==========
# def extract_medical_entities(text_list):
#     text = " ".join(text_list)
#     ents = ner_pipeline(text)
#     results = [
#         (ent['word'], ent['entity_group'], round(ent['score'], 2))
#         for ent in ents if ent['score'] > 0.85
#     ]
#     return results

# ========== Main Pipeline ==========
def OcrPrescription(img_path):
    logging.info("Performing OCR...")
    raw_lines = ocr_image_with_gemini(img_path)
    logging.info(f"OCR lines: {raw_lines}")

    cleaned_line = clean_text_lines(raw_lines)
    logging.info(f"OCR lines: {cleaned_line}")

    corrected = correct_text(cleaned_line, medical_dict)
    logging.info(f"Corrected: {corrected}")

    return {
        "ocr_lines": raw_lines,
        "Matched_Drugs": corrected
    }
