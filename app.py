# app.py
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import check_password_hash
import json, sqlite3, time, os
import spacy
from utils import split_sentences, load_pairs, get_next_paragraph, calculate_score
import csv
from flask import render_template_string, Response
import io

app = Flask(__name__)
app.secret_key = 'secret!'
socketio = SocketIO(app)

nlp = spacy.load("en_core_web_sm")
pairs = load_pairs()

online_users = {}
current_tasks = {}
selections = {}
confirmations = {}
attempts = {}  # 新增：记录每个room的尝试次数
attempt_logs = {}  # 新增：记录每次尝试的细节

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('/data/game.db')
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

@socketio.on('join')
def handle_join(data):
    username = data['username']
    online_users[username] = request.sid
    partner = pairs.get(username)
    if not partner:
        return
    room = f'{username}_{partner}' if username < partner else f'{partner}_{username}'
    join_room(room)

    if room not in current_tasks:
        current_tasks[room] = get_next_paragraph(room)
        attempts[room] = 0
        attempt_logs[room] = []

    paragraph = current_tasks[room]
    sentence_list = split_sentences(paragraph['text'])
    socketio.emit('start_task', {
        'paragraph': paragraph,
        'sentences': sentence_list
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

    # 双方都提交
    p1, p2 = username, partner
    if p2 not in selections[room]:
        return  # 避免错误

    s1 = set(selections[room][p1]['selected'])
    s2 = set(selections[room][p2]['selected'])

    dur1 = selections[room][p1]['duration']
    dur2 = selections[room][p2]['duration']

    is_match = s1 == s2
    attempts[room] += 1

    # 添加到日志
    attempt_logs[room].append({
        'attempt': attempts[room],
        'selections': {
            p1: list(s1),
            p2: list(s2)
        },
        'durations': {
            p1: dur1,
            p2: dur2
        },
        'match': is_match
    })

    if is_match or attempts[room] >= 3:
        score1 = calculate_score(len(s1), dur1)
        score2 = calculate_score(len(s2), dur2)

        conn = sqlite3.connect('/data/game.db')
        c = conn.cursor()
        if is_match:
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score1, p1))
            c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score2, p2))

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

        # 进入下一个段落
        current_tasks[room] = get_next_paragraph(room)
        sentence_list = split_sentences(current_tasks[room]['text'])
        selections[room] = {}
        confirmations[room] = set()
        attempts[room] = 0
        attempt_logs[room] = []

        socketio.emit('start_task', {
            'paragraph': current_tasks[room],
            'sentences': sentence_list
        }, room=room)
    else:
        # 匹配失败但还没到三次，通知失败，继续选
        socketio.emit('attempt_failed', {
            'remaining': 3 - attempts[room]
        }, room=room)
        confirmations[room] = set()

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('/data/game.db')
    c = conn.cursor()
    c.execute('SELECT username, total_score FROM users WHERE role="player" ORDER BY total_score DESC')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

@app.route("/admin/users")
def admin_users():
    conn = sqlite3.connect('/data/game.db')
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
    conn = sqlite3.connect('/data/game.db')
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
def download_users_csv():
    conn = sqlite3.connect('/data/game.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role, total_score FROM users")
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Role', 'Score'])
    writer.writerows(rows)

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=users.csv"
    return response

@app.route("/admin/download-matches")
def download_matches_csv():
    conn = sqlite3.connect('/data/game.db')
    c = conn.cursor()
    c.execute('''SELECT id, paragraph_id, player1, player2, selections_p1, selections_p2,
                        is_match, score_p1, score_p2, duration_p1, duration_p2, timestamp
                 FROM matches''')
    rows = c.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Paragraph ID', 'Player 1', 'Player 2', 'Selections P1', 'Selections P2',
                     'Is Match', 'Score P1', 'Score P2', 'Duration P1', 'Duration P2', 'Timestamp'])
    writer.writerows(rows)

    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=matches.csv"
    return response
#local:
# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5001))
#     socketio.run(app, debug=True, host="0.0.0.0", port=port, use_reloader=False)
#
#server:
import eventlet
eventlet.monkey_patch()
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, debug=False, host="0.0.0.0", port=port)
