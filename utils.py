# === 文件: utils.py ===
import json, sqlite3
import spacy
nlp = spacy.load("en_core_web_sm")
DB_PATH = "/data/game.db"

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
    with open('data/paragraphs.json', 'r') as f:
        paragraphs = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT paragraph_index FROM progress WHERE room = ?', (room,))
    row = c.fetchone()

    if row:
        index = row[0] + 1
    else:
        index = 0

    if index >= len(paragraphs):
        conn.close()
        return {'id': -1, 'text': 'No more paragraphs.'}

    # 更新段落进度
    c.execute('INSERT OR REPLACE INTO progress (room, paragraph_index) VALUES (?, ?)', (room, index))
    conn.commit()
    conn.close()

    paragraph = paragraphs[index]
    return {
        'id': paragraph['id'],
        'text': paragraph['text']
    }

def calculate_score(num_sentences, duration):
    base = num_sentences
    time_factor = 1 + max(0, (60 - duration) / 60)
    return round(base * time_factor, 2)