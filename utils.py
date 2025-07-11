import json
import sqlite3
import spacy
import os
from config import DB_PATH

nlp = spacy.load("en_core_web_sm")

# 加载 pairs
def load_pairs():
    with open("data/pairs.json") as f:
        return json.load(f)

def split_sentences(paragraph_text):
    doc = nlp(paragraph_text)
    return [sent.text.strip() for sent in doc.sents]

# 加载 room 到 paragraph 文件名的映射
with open("data/paragraph_map.json", "r") as f:
    PARAGRAPH_MAP = json.load(f)

# 缓存段落数据，避免重复读取
PARAGRAPH_CACHE = {}

def get_paragraphs_for_room(room):
    fname = PARAGRAPH_MAP.get(room, "paragraphs.json")
    if fname not in PARAGRAPH_CACHE:
        with open(os.path.join("data", fname), "r", encoding="utf-8") as f:
            PARAGRAPH_CACHE[fname] = json.load(f)
    return PARAGRAPH_CACHE[fname]

def get_paragraph_by_index(room, index):
    paragraphs = get_paragraphs_for_room(room)
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
    return get_paragraph_by_index(room, index)

def calculate_relative_score(duration1, duration2):
    # 限制范围在 [0.01, 1200]
    duration1 = min(max(duration1, 0.01), 1200)
    duration2 = min(max(duration2, 0.01), 1200)
    # 限制比例不超过 9999:1
    ratio = max(duration1 / duration2, duration2 / duration1)
    if ratio > 9999:
        if duration1 > duration2:
            duration1 = duration2 * 9999
        else:
            duration2 = duration1 * 9999
    total = duration1 + duration2
    if total == 0:
        return 0.5, 0.5  # 平分
    score1 = duration2 / total
    score2 = duration1 / total
    return round(score1, 5), round(score2, 5)

def get_total_paragraphs():
    with open('data/paragraphs_team1.json') as f:
        data = json.load(f)
    return len(data)