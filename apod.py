# all the imports
import os
import time
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

    cur.execute('SELECT msg_id, title, date::date, text FROM apod ORDER BY date DESC LIMIT 10')
    entries = cur.fetchall()
    return render_template('show_apods.html', entries=entries)

@app.route('/search', methods=['GET'])
def search():
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    order = request.args['order']

    # Prepare the query
    if order == 'rank':
        rank_func = request.args['rank_func']

        if rank_func == 'ts_rank':
            query = ("SELECT msg_id, title, date, ts_headline('apod_conf', text, "
                "        to_tsquery('apod_conf', %(pat)s)) AS text \n"
                " FROM (SELECT msg_id, title, date::date, text \n"
                "       FROM apod \n"
                "       WHERE fts @@ to_tsquery('apod_conf', %(pat)s) \n"
                "       ORDER BY ts_rank(fts, to_tsquery('apod_conf', %(pat)s)) DESC \n"
                "       LIMIT 10) AS entries")
        elif rank_func == 'ts_rank_cd':
            query = ("SELECT msg_id, title, date, ts_headline('apod_conf', text, "
                "        to_tsquery('apod_conf', %(pat)s)) AS text \n"
                " FROM (SELECT msg_id, title, date::date, text \n"
                "       FROM apod \n"
                "       WHERE fts @@ to_tsquery('apod_conf', %(pat)s) \n"
                "       ORDER BY ts_rank_cd(fts, to_tsquery('apod_conf', %(pat)s)) DESC \n"
                "       LIMIT 10) AS entries")
        else:
            query = ("SELECT msg_id, title, date, ts_headline('apod_conf', text, "
                "        to_tsquery('apod_conf', %(pat)s)) AS text \n"
                " FROM (SELECT msg_id, title, date::date, text \n"
                "       FROM apod \n"
                "       WHERE fts @@ to_tsquery('apod_conf', %(pat)s) \n"
                "       ORDER BY fts <=> to_tsquery('apod_conf', %(pat)s) \n"
                "       LIMIT 10) AS entries")
    else:
        query = ("SELECT msg_id, title, date, ts_headline('apod_conf', text, "
                "        to_tsquery('apod_conf', %(pat)s)) AS text \n"
                " FROM (SELECT msg_id, title, date::date, text \n"
                "       FROM apod \n"
                "       WHERE fts @@ to_tsquery('apod_conf', %(pat)s) \n"
                "       ORDER BY date DESC \n"
                "       LIMIT 10) AS entries")

    # Prepare the query to show to user
    query_text = query % {"pat": "'%s'" % (request.args['pattern'])}
    query_text = query_text.replace("\n", "<br>")

    # Show time to user
    starttime = time.time()
    cur.execute(query, {"pat": request.args['pattern']})
    query_time = "%0.2f" % ((time.time() - starttime) * 1000)

    entries = cur.fetchall()
    return render_template(
        'show_apods.html',
        entries=entries,
        pattern=request.args['pattern'],
        query_text=query_text,
        query_time=query_time)

@app.route('/apod/<int:apod_id>')
def show_apod(apod_id):
    db = get_db()
    cur = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    query = ("SELECT title, date::date, text "
            " FROM apod WHERE msg_id = %s")

    cur.execute(query, [apod_id])

    entry = cur.fetchone()
    return render_template(
        'show_apod.html',
        entry=entry)