# all the imports
import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

# create our apod application
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development-key',
    DATABASE = 'apod',
    HOST = 'localhost',
    PORT = 5432
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    conn = psycopg2.connect(
        database = app.config['DATABASE'],
        host = app.config['HOST'],
        port = app.config['PORT'])
    conn.autocommit = True
    return conn

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'pg_db'):
        g.pg_db = connect_db()
    return g.pg_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'pg_db'):
        g.pg_db.close()

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT title, date::date, text FROM apod ORDER BY date DESC LIMIT 10')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/search', methods=['GET'])
def search():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    search_type = request.args['type']
    order = request.args['order']

    if search_type == 'simple':
        if order == 'rank':
            query = ("SELECT title, date, ts_headline('apod_conf', text, q) AS text "
                    " FROM (SELECT title, date::date, text, q "
                    "       FROM apod, plainto_tsquery('apod_conf', %s) AS q "
                    "       WHERE fts @@ q "
                    "       ORDER BY ts_rank_cd(fts, q) DESC "
                    "       LIMIT 10) AS entries")
        else:
            query = ("SELECT title, date, ts_headline('apod_conf', text, q) AS text "
                    " FROM (SELECT title, date::date, text, q "
                    "       FROM apod, plainto_tsquery('apod_conf', %s) AS q "
                    "       WHERE fts @@ q "
                    "       ORDER BY date DESC "
                    "       LIMIT 10) AS entries")
    else:
        if order == 'rank':
            query = ("SELECT title, date, ts_headline('apod_conf', text, q) AS text "
                    " FROM (SELECT title, date::date, text, q "
                    "       FROM apod, plainto_tsquery('apod_conf', %s) AS q "
                    "       WHERE fts @@ q "
                    "       ORDER BY fts <=> q "
                    "       LIMIT 10) AS entries")
        else:
            query = ("SELECT title, date, ts_headline('apod_conf', text, q) AS text "
                    " FROM (SELECT title, date::date, text, q "
                    "       FROM apod, plainto_tsquery('apod_conf', %s) AS q "
                    "       WHERE fts @@ q "
                    "       ORDER BY date DESC "
                    "       LIMIT 10) AS entries")

    cur.execute(query, [request.args['pattern']])
    entries = cur.fetchall()
    return render_template(
        'show_entries.html',
        entries=entries,
        pattern=request.args['pattern'])
