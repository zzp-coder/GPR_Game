import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request, redirect, session, jsonify, render_template_string, send_file, render_template
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import check_password_hash
import json, sqlite3, time, os, io
import spacy
from utils import split_sentences, load_pairs, get_or_create_progress, get_paragraph_by_index, advance_progress, calculate_relative_score
from config import DB_PATH
import shutil

app = Flask(__name__)
app.secret_key = 'secret!'
socketio = SocketIO(app)

nlp = spacy.load("en_core_web_sm")
pairs = load_pairs()

online_users = {}
current_tasks = {}
selections = {}
confirmations = {}
attempts = {}
attempt_logs = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT password, role FROM users WHERE username=?', (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['username'] = username
            session['role'] = row[1]
            return redirect('/admin' if row[1] == 'admin' else '/game')
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/game')
def game():
    if 'username' not in session:
        return redirect('/')
    return render_template('game.html', username=session['username'])

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template('admin.html')

@app.route('/admin/online')
def admin_online():
    html = "<h3>Online Users</h3><table><tr><th>Username</th><th>Socket ID</th></tr>"
    for u, sid in online_users.items():
        html += f"<tr><td>{u}</td><td>{sid}</td></tr>"
    html += "</table><a href='/admin'>Back to Admin</a>"
    return render_template_string(html)

@socketio.on('join')
def handle_join(data):
    username = data['username']
    online_users[username] = request.sid
    partner = pairs.get(username)
    if not partner:
        return
    room = f'{username}_{partner}' if username < partner else f'{partner}_{username}'
    join_room(room)

    if partner not in online_users:
        socketio.emit('waiting_partner', {}, to=request.sid)
        return

    if room not in current_tasks:
        index = get_or_create_progress(room)
        current_tasks[room] = get_paragraph_by_index(room, index)
        attempts[room] = 0
        attempt_logs[room] = []

    paragraph = current_tasks[room]
    if paragraph['id'] == -1:
        socketio.emit('start_task', {'done': True}, room=room)
    else:
        sentence_list = split_sentences(paragraph['text'])
        index = get_or_create_progress(room)
        socketio.emit('start_task', {
            'paragraph': paragraph,
            'sentences': sentence_list,
            'total': 1000,
            'current_index': index
        }, room=room)

@socketio.on('submit_selection')
def handle_submit(data):
    username = data['username']
    partner = pairs[username]
    room = f'{username}_{partner}' if username < partner else f'{partner}_{username}'

    now = time.time()
    selections.setdefault(room, {})[username] = {
        'selected': data['selected'],
        'duration': now - data['start_time']
    }
    confirmations.setdefault(room, set()).add(username)

    if len(confirmations[room]) < 2:
        return

    p1, p2 = username, partner
    if p2 not in selections[room]:
        return

    s1 = set(selections[room][p1]['selected'])
    s2 = set(selections[room][p2]['selected'])

    dur1 = selections[room][p1]['duration']
    dur2 = selections[room][p2]['duration']

    is_match = s1 == s2
    attempts[room] += 1

    attempt_logs[room].append({
        'attempt': attempts[room],
        'selections': {p1: list(s1), p2: list(s2)},
        'durations': {p1: dur1, p2: dur2},
        'match': is_match
    })

    if is_match or attempts[room] >= 3:
        score1, score2 = calculate_relative_score(dur1, dur2)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if is_match:
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score1, p1))
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score2, p2))

        progress_index = get_or_create_progress(room)
        if progress_index > 0 and progress_index % 1000 == 0:
            bonus = 50
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (bonus, p1))
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (bonus, p2))

        c.execute('''INSERT INTO matches
                     (paragraph_id, player1, player2, is_match, selections_p1, selections_p2,
                      score_p1, score_p2, duration_p1, duration_p2, attempts_json)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (current_tasks[room]['id'], p1, p2, is_match,
                   json.dumps(list(s1)), json.dumps(list(s2)),
                   score1 if is_match else 0, score2 if is_match else 0,
                   dur1, dur2, json.dumps(attempt_logs[room])))
        conn.commit()
        conn.close()

        current_tasks[room] = advance_progress(room)
        if current_tasks[room]['id'] == -1:
            socketio.emit('start_task', {'done': True}, room=room)
        else:
            sentence_list = split_sentences(current_tasks[room]['text'])
            selections[room] = {}
            confirmations[room] = set()
            attempts[room] = 0
            attempt_logs[room] = []
            index = get_or_create_progress(room)
            socketio.emit('start_task', {
                'paragraph': current_tasks[room],
                'sentences': sentence_list,
                'total': 1000,
                'current_index': index
            }, room=room)
    else:
        socketio.emit('attempt_failed', {
            'remaining': 3 - attempts[room]
        }, room=room)
        confirmations[room] = set()

@app.route("/game-finished")
def game_finished():
    return render_template("success.html")

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, total_score FROM users WHERE role="player" ORDER BY total_score DESC')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route("/admin/users")
def admin_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, role, total_score FROM users ORDER BY total_score DESC")
    rows = c.fetchall()
    conn.close()
    html = "<h3>All Users</h3><table><tr><th>ID</th><th>Username</th><th>Role</th><th>Score</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]:.1f}</td></tr>"
    html += "</table><a href='/admin'>Back to Admin</a>"
    return render_template_string(html)

@app.route("/admin/matches")
def admin_matches():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, paragraph_id, player1, player2, selections_p1, selections_p2,
                        is_match, score_p1, score_p2, duration_p1, duration_p2, timestamp
                 FROM matches ORDER BY timestamp DESC''')
    rows = c.fetchall()
    conn.close()
    html = "<h3>All Matches</h3><table><tr><th>ID</th><th>Paragraph</th><th>Player 1</th><th>Player 2</th><th>Selections P1</th><th>Selections P2</th><th>Match?</th><th>Score P1</th><th>Score P2</th><th>Dur P1</th><th>Dur P2</th><th>Time</th></tr>"
    for row in rows:
        html += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td><td>{'✅' if row[6] else '❌'}</td><td>{row[7]}</td><td>{row[8]}</td><td>{row[9]}</td><td>{row[10]}</td><td>{row[11]}</td></tr>"
    html += "</table><a href='/admin'>Back to Admin</a>"
    return render_template_string(html)

@app.route("/admin/download-users")
def download_users_json():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, role, total_score FROM users")
    rows = c.fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "username": r[1], "role": r[2], "score": r[3]} for r in rows
    ])

@app.route("/admin/download-matches")
def download_matches_json():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, paragraph_id, player1, player2, selections_p1, selections_p2,
                        is_match, score_p1, score_p2, duration_p1, duration_p2, attempts_json, timestamp
                 FROM matches''')
    rows = c.fetchall()
    conn.close()
    return jsonify([
        {
            "id": r[0],
            "paragraph_id": r[1],
            "player1": r[2],
            "player2": r[3],
            "selections_p1": json.loads(r[4]),
            "selections_p2": json.loads(r[5]),
            "is_match": bool(r[6]),
            "score_p1": r[7],
            "score_p2": r[8],
            "duration_p1": r[9],
            "duration_p2": r[10],
            "attempts": json.loads(r[11]),
            "timestamp": r[12]
        } for r in rows
    ])

@app.route("/admin/download-db")
def download_db():
    return send_file(DB_PATH, as_attachment=True, download_name="game.db")

@app.route("/admin/reset-db", methods=["GET", "POST"])
def admin_reset_db():
    if session.get('role') != 'admin':
        return redirect('/')

    if request.method == "POST":
        if os.path.exists(DB_PATH):
            shutil.copy(DB_PATH, DB_PATH + ".bak")

        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

        os.system("python3 init_db.py")

        return render_template_string("""
        <h3>✅ 数据库已重置</h3>
        <p>旧数据库已备份为 <code>game.db.bak</code></p>
        <p><a href='/admin'>返回 Admin 面板</a></p>
        """)

    return render_template_string("""
    <h3>⚠️ 确认要重置数据库？</h3>
    <p>这将删除所有用户数据、得分和配对记录。</p>
    <form method="post">
        <button type="submit">🧨 确认重置数据库</button>
        <a href="/admin">取消</a>
    </form>
    """)

@app.route("/how-to-play")
def how_to_play():
    return render_template("how_to_play.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, debug=False, host="0.0.0.0", port=port)