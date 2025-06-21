from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import check_password_hash
import json, sqlite3, time, os
import spacy
from utils import split_sentences, load_pairs, get_next_paragraph, calculate_score

app = Flask(__name__)
app.secret_key = 'secret!'
socketio = SocketIO(app)

nlp = spacy.load("en_core_web_sm")

pairs = load_pairs()

online_users = {}
current_tasks = {}
selections = {}
confirmations = {}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('db/game.db')
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

    if len(confirmations[room]) == 2:
        s1 = set(selections[room][username]['selected'])
        s2 = set(selections[room][partner]['selected'])
        match = s1 == s2
        dur_u = selections[room][username]['duration']
        dur_p = selections[room][partner]['duration']
        score_u = calculate_score(len(s1), dur_u)
        score_p = calculate_score(len(s2), dur_p)

        conn = sqlite3.connect('db/game.db')
        c = conn.cursor()
        c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score_u, username))
        c.execute('UPDATE users SET total_score = total_score + ? WHERE username = ?', (score_p, partner))
        c.execute('''INSERT INTO matches
                  (paragraph_id, player1, player2, selections_p1, selections_p2,
                   is_match, score_p1, score_p2, duration_p1, duration_p2)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (current_tasks[room]['id'], username, partner,
                   json.dumps(list(s1)), json.dumps(list(s2)), match,
                   score_u, score_p, dur_u, dur_p))
        conn.commit()
        conn.close()

        current_tasks[room] = get_next_paragraph(room)
        sentence_list = split_sentences(current_tasks[room]['text'])
        confirmations[room] = set()
        socketio.emit('start_task', {
            'paragraph': current_tasks[room],
            'sentences': sentence_list
        }, room=room)

@app.route('/leaderboard')
def leaderboard():
    conn = sqlite3.connect('db/game.db')
    c = conn.cursor()
    c.execute('SELECT username, total_score FROM users WHERE role="player" ORDER BY total_score DESC')
    data = c.fetchall()
    conn.close()
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    socketio.run(app, debug=True, host="0.0.0.0", port=port, use_reloader=False)