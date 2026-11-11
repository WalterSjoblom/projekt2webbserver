from flask import Flask, session, redirect, url_for, request
import mysql.connector

app = Flask(__name__)
app.secret_key = 'supersecretkey'


def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='forum'
    )


def query(sql, params=(), write=False):
    """Kor en SQL-fraga. Vid INSERT returneras id pa nya raden, annars alla rader."""
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if write:
            conn.commit()
            return cur.lastrowid
        return cur.fetchall()
    finally:
        conn.close()


def sida(titel, innehall):
    """Lagger menyn och stilmallen runt innehallet sa att alla sidor ser likadana ut."""
    if 'username' in session:
        meny = f'Inloggad som <b>{session["username"]}</b> <a href="/logout">Logga ut</a>'
    else:
        meny = '<a href="/login">Logga in</a>'

    return f'''
        <!DOCTYPE html>
        <html lang="sv">
        <head>
            <meta charset="UTF-8">
            <title>{titel}</title>
            <link rel="stylesheet" href="/static/style.css">
        </head>
        <body>
            <nav><a href="/">Forum for farskallar</a><span>{meny}</span></nav>
            {innehall}
        </body>
        </html>
    '''


@app.route('/')
def startsida():
    tradar = query('''
        SELECT topics.id, topics.title, users.username
        FROM topics JOIN users ON users.id = topics.user_id
        ORDER BY topics.id DESC
    ''')

    lista = ''
    for trad in tradar:
        lista += f'<li><a href="/trad/{trad["id"]}">{trad["title"]}</a> (startad av {trad["username"]})</li>'
    if not tradar:
        lista = '<p>Har var det tomt! Bli forst med att starta en trad.</p>'

    if 'user_id' in session:
        ny_trad = '''
            <h2>Starta en ny trad</h2>
            <form method="post" action="/ny-trad">
                Rubrik: <input type="text" name="rubrik">
                Din fraga: <textarea name="text" rows="5"></textarea>
                <input type="submit" value="Starta tradden">
            </form>
        '''
    else:
        ny_trad = '<p><a href="/login">Logga in</a> om du vill starta en egen trad.</p>'

    return sida('Forum for farskallar', f'<h1>Alla tradar</h1><ul>{lista}</ul>{ny_trad}')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        anvandare = query(
            'SELECT id, username FROM users WHERE username = %s AND password = %s',
            (request.form['username'], request.form['password'])
        )
        if anvandare:
            session['user_id'] = anvandare[0]['id']
            session['username'] = anvandare[0]['username']
            return redirect(url_for('startsida'))
        return sida('Logga in', '<p>Hoppsan, fel anvandarnamn eller losenord. <a href="/login">Forsok igen</a></p>')

    return sida('Logga in', '''
        <h1>Logga in</h1>
        <form method="post">
            Anvandarnamn: <input type="text" name="username">
            Losenord: <input type="password" name="password">
            <input type="submit" value="Logga in">
        </form>
        <p><i>Testa: holros/foo, manfol/bar eller goskor/baz</i></p>
    ''')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('startsida'))


@app.route('/ny-trad', methods=['POST'])
def ny_trad():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    trad_id = query(
        'INSERT INTO topics (title, user_id) VALUES (%s, %s)',
        (request.form['rubrik'], session['user_id']),
        write=True
    )
    # Fragan som skrevs i formularet blir det forsta inlagget i tradden
    query(
        'INSERT INTO posts (topic_id, user_id, text) VALUES (%s, %s, %s)',
        (trad_id, session['user_id'], request.form['text']),
        write=True
    )
    return redirect(url_for('visa_trad', trad_id=trad_id))


@app.route('/trad/<int:trad_id>')
def visa_trad(trad_id):
    tradar = query('SELECT title FROM topics WHERE id = %s', (trad_id,))
    if not tradar:
        return sida('Hittades inte', '<p>Den har tradden finns inte. <a href="/">Tillbaka till alla tradar</a></p>')

    inlagg = query('''
        SELECT posts.text, posts.created_at, users.username
        FROM posts JOIN users ON users.id = posts.user_id
        WHERE posts.topic_id = %s
        ORDER BY posts.id
    ''', (trad_id,))

    alla_inlagg = ''
    for i in inlagg:
        alla_inlagg += f'''
            <div class="inlagg">
                <small><b>{i["username"]}</b> skrev {i["created_at"]}</small>
                <p>{i["text"]}</p>
            </div>
        '''

    if 'user_id' in session:
        svarsruta = f'''
            <h2>Skriv ett svar</h2>
            <form method="post" action="/svara/{trad_id}">
                <textarea name="text" rows="5"></textarea>
                <input type="submit" value="Skicka svar">
            </form>
        '''
    else:
        svarsruta = '<p><a href="/login">Logga in</a> om du vill svara.</p>'

    return sida(tradar[0]['title'], f'<h1>{tradar[0]["title"]}</h1>{alla_inlagg}{svarsruta}')


@app.route('/svara/<int:trad_id>', methods=['POST'])
def svara(trad_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query(
        'INSERT INTO posts (topic_id, user_id, text) VALUES (%s, %s, %s)',
        (trad_id, session['user_id'], request.form['text']),
        write=True
    )
    # Tillbaka till tradden sa att sidan inte skickar svaret igen vid omladdning
    return redirect(url_for('visa_trad', trad_id=trad_id))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')