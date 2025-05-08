from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
import os
import psycopg2
import validators
from datetime import datetime
from urllib.parse import urlparse

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')

def get_db():
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/urls', methods=['GET'])
def urls():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, name, created_at FROM urls ORDER BY created_at DESC;')
    urls = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('urls.html', urls=urls)


@app.route('/urls/<int:id>')
def url_detail(id):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM urls WHERE id = %s', (id,))
            url = cur.fetchone()

        return render_template('detail.html', url=url) if url else abort(404)

    except psycopg2.Error as e:
        app.logger.error(f'Database error: {str(e)}')
        abort(500)
    finally:
        release_db(conn)

@app.route('/urls', methods=['POST'])
def add_url():
    raw_url = request.form.get('url', '').strip()
    errors = validate_url(raw_url)
    if errors:
        flash(errors['name'], 'danger')
        return render_template('index.html', url=raw_url, errors=errors), 422

    parsed_url = urlparse(raw_url)
    normalized_url = f'{parsed_url.scheme}://{parsed_url.netloc}'

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            'INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id;',
            (normalized_url, datetime.now())
        )
        url_id = cur.fetchone()[0]
        conn.commit()
        flash('Сайт успешно добавлен', 'success')
        return redirect(url_for('url_detail', id=url_id))
    except psycopg2.IntegrityError:
        conn.rollback()
        cur.execute('SELECT id FROM urls WHERE name = %s;', (normalized_url,))
        url_id = cur.fetchone()[0]
        flash('Страница уже существует', 'info')
        return redirect(url_for('url_detail', id=url_id))
    finally:
        cur.close()
        conn.close()

def validate_url(url):
    errors = {}
    if not url:
        errors['name'] = 'URL обязателен'
    elif len(url) > 255:
        errors['name'] = 'URL превышает 255 символов'
    elif not validators.url(url):
        errors['name'] = 'Некорректный URL'
    return errors