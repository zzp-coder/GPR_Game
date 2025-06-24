# === 文件: utils.py ===
import json, sqlite3
import spacy
nlp = spacy.load("en_core_web_sm")
from config import DB_PATH

with open("data/paragraphs.json") as f:
    all_paragraphs = json.load(f)

used_paragraphs = {}

def load_pairs():
    with open("data/pairs.json") as f:
        return json.load(f)

def split_sentences(paragraph_text):
    doc = nlp(paragraph_text)
    return [sent.text.strip() for sent in doc.sents]


def get_paragraph_by_index(index):
    with open('data/paragraphs.json', 'r') as f:
        paragraphs = json.load(f)

    if index >= len(paragraphs):
        return {'id': -1, 'text': 'No more paragraphs.'}

    return {
        'id': paragraphs[index]['id'],
        'text': paragraphs[index]['text']
    }


def get_or_create_progress(room):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT paragraph_index FROM progress WHERE room = ?', (room,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def advance_progress(room):
    index = get_or_create_progress(room) + 1
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO progress (room, paragraph_index) VALUES (?, ?)', (room, index))
    conn.commit()
    conn.close()
    return get_paragraph_by_index(index)

def calculate_score(num_sentences, duration):
    base = num_sentences
    time_factor = 1 + max(0, (60 - duration) / 60)
    return round(base * time_factor, 2)