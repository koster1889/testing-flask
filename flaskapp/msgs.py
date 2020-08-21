from flask import Blueprint
from flask import render_template
from flaskapp.db import get_db
from flask import app, request, redirect, url_for, flash, session, g
from .auth import login_required

bp = Blueprint('message', __name__)

@bp.route('/')
def index():
    convos = {}
    if g.user is not None:
        convos = get_conversations()
    return render_template('msgs/index.html', convos=convos)


@bp.route('/users')
def users():
    db = get_db()
    users = db.execute(
        'SELECT username '
        'FROM user ORDER BY username DESC'
    ).fetchall()
    return render_template('msgs/users.html', users=users)


@bp.route('/send', methods=("POST", "GET"))
@login_required
def create():
    if request.method == 'POST':
        error = None
        recipient_username = request.form['to_username']
        message_body = request.form['body']

        recipient_id = get_user(recipient_username)

        if not recipient_id:
            error = 'User "{}" does not exist'.format(recipient_username)

        create_message(recipient_id, message_body)

        if error is None:
            return redirect(url_for('message.index'))

        flash(error)

    return render_template('msgs/send.html')


def get_conversations():
    user_id = g.user['id']
    db = get_db()
    messages = db.execute(
        'SELECT body, from_id, to_id, uto.username AS to_username, ufrom.username AS from_username, body FROM msgs m '
        ' JOIN user uto ON m.to_id = uto.id '
        ' JOIN user ufrom ON m.from_id = ufrom.id '
        'WHERE from_id = ? OR to_id = ?', (user_id, user_id)
    ).fetchall()

    conversations = {}

    for message in messages:
        conversation_username = message['from_username'] \
                                    if message['from_username'] != g.user['username'] \
                                    else message['to_username']
        
        if conversation_username not in conversations:
            conversations[conversation_username] = []
        
        conversations[conversation_username].append(message)

    return conversations



def create_message(id, body):
    my_id = session.get('user_id')
    db = get_db()
    db.execute('INSERT INTO msgs (from_id, to_id, body) VALUES (?, ?, ?)', (my_id, id, body))
    db.commit()

def get_user(username):
    db = get_db()

    user = db.execute('SELECT id FROM user WHERE username = ?', (username,)).fetchone()

    if user is not None:
        return user['id']
    else:
        return None
