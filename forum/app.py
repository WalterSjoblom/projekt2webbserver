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
