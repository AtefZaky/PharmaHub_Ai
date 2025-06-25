import easyocr
import cv2
import matplotlib.pyplot as plt
import pandas as pd
from rapidfuzz import process, fuzz
import re

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# === Step 1: Load drugs from Excel column 'name' ===
def load_drug_list_from_excel(file_path):
    df = pd.read_excel(file_path)
    drug_list = df["name"].dropna().astype(str).tolist()
    return drug_list

drug_list = load_drug_list_from_excel("Drug_DataBase.xlsx")

# === Embedding + FAISS Setup with Cosine Similarity ===
model = SentenceTransformer('all-MiniLM-L6-v2')
drug_embeddings = model.encode(drug_list, convert_to_numpy=True)
drug_embeddings = drug_embeddings / np.linalg.norm(drug_embeddings, axis=1, keepdims=True)

dimension = drug_embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)  # Use cosine similarity
index.add(drug_embeddings)

# === Token Cleaner ===
def clean_ocr_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\u0600-\u06FF\s\-]', ' ', text)  # Keep Arabic + English letters, remove numbers/symbols
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# === Matching OCR Tokens to Drug Embeddings ===
def match_ocr_text_to_drugs(ocr_text, top_k=1, similarity_threshold=0.75):
    matched = []
    unmatched = []

    clean_text = clean_ocr_text(ocr_text)
    tokens = clean_text.split()

    for token in tokens:
        print(f"Processing token: {token}")
        query_embedding = model.encode([token], convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)

        distances, indices = index.search(query_embedding, top_k)
        best_idx = indices[0][0]
        similarity = distances[0][0]  # Already cosine similarity in range [-1, 1]

        if similarity > similarity_threshold:
            matched.append((token, drug_list[best_idx], float(round(similarity, 2))))
        else:
            unmatched.append(token)

    return matched, unmatched

# === Test Example ===
ocr_text = "Paracetmol Ibuprofine Metphormin unknown"
matches, not_found = match_ocr_text_to_drugs(ocr_text)

print("✅ Matches:")
for original, matched_drug, score in matches:
    print(f"- OCR: {original} → Match: {matched_drug} (score: {score})")

print("\n❌ Not Found:")
print(", ".join(not_found))


# === Text Simplification for Later Use (Placeholder) ===
def simplify_name(text):
    return text


# === EasyOCR Extraction Function ===
def process_prescription(file_path: str):
    """
    Processes a prescription image to extract text and identify drugs.
    """
    reader = easyocr.Reader(['en'])  # Or ['en', 'ar'] for Arabic
    results = reader.readtext(file_path, detail=0)
    extracted_text = "\n".join(results)
    print(extracted_text)
    return {"extracted_text": extracted_text}


# === High-Level Matching Function (for use in routes) ===
def match_drugs(extracted_text):
    """
    Matches extracted text against a predefined list of drugs.
    """
    # Simulate OCR result (replace in actual usage)
    ocr_text = "paracetamol Ibuprofine Metphormin unknown"
    # ocr_text = extracted_text  # Use directly instead of hardcoded string

    matches, not_found = match_ocr_text_to_drugs(ocr_text)

    print("✅ Matches:")
    for original, matched_drug, score in matches:
        print(f"- OCR: {original} → Match: {matched_drug} (score: {score})")

    return matches
