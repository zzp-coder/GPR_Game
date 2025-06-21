# === 文件: utils.py ===
import json, os, sqlite3
import spacy
nlp = spacy.load("en_core_web_sm")

with open("data/paragraphs.json") as f:
    all_paragraphs = json.load(f)

used_paragraphs = {}

def load_pairs():
    with open("data/pairs.json") as f:
        return json.load(f)

def split_sentences(paragraph_text):
    doc = nlp(paragraph_text)
    return [sent.text.strip() for sent in doc.sents]

def get_next_paragraph(room):
    used = used_paragraphs.get(room, set())
    for para in all_paragraphs:
        if para['id'] not in used:
            used_paragraphs.setdefault(room, set()).add(para['id'])
            return para
    return {"id": -1, "text": "No more paragraphs."}

def calculate_score(num_sentences, duration):
    base = num_sentences
    time_factor = 1 + max(0, (60 - duration) / 60)
    return round(base * time_factor, 2)