import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
from datetime import datetime, timedelta, timezone

# 日本時間（UTC+9）
JST = timezone(timedelta(hours=9))

app = Flask(__name__)

# Renderの環境変数からIDとパスワードを取得
USERNAME = os.environ.get("BASIC_AUTH_USERNAME")
PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD")

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
        '認証が必要です。IDとパスワードを入力してください。', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# 以下は既存のDB設定・関数

DB_NAME = "todo.db"

CATEGORY_COLORS = {
    "仕事": "primary",
    "買い物": "warning",
    "趣味": "success",
    "スキル": "info",
    "予定": "danger",
}

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)
    conn.execute("INSERT OR IGNORE INTO categories (name) VALUES ('仕事'), ('買い物'), ('趣味'), ('スキル'), ('予定')")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        category_id INTEGER,
        created_at TEXT NOT NULL,
        is_done INTEGER DEFAULT 0,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )
    """)
    conn.commit()
    conn.close()

@app.route("/")
@requires_auth
def index():
    keyword = request.args.get("q", "").strip()
    conn = get_db_connection()
    tasks = conn.execute("""
        SELECT tasks.*, categories.name AS category_name
        FROM tasks LEFT JOIN categories ON tasks.category_id = categories.id
        ORDER BY created_at DESC
    """).fetchall()
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()
    return render_template("index.html", tasks=tasks, categories=categories, keyword=keyword, category_colors=CATEGORY_COLORS)

@app.route("/add", methods=["POST"])
@requires_auth
def add():
    task = request.form["task"]
    category_id = request.form.get("category_id")
    if task:
        now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO tasks (content, created_at, category_id) VALUES (?, ?, ?)",
            (task, now, category_id if category_id else None)
        )
        conn.commit()
        conn.close()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
@requires_auth
def delete(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>")
@requires_auth
def toggle(task_id):
    conn = get_db_connection()
    task = conn.execute("SELECT is_done FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task:
        new_status = 0 if task["is_done"] else 1
        conn.execute("UPDATE tasks SET is_done = ? WHERE id = ?", (new_status, task_id))
        conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@requires_auth
def edit(task_id):
    conn = get_db_connection()
    task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    categories = conn.execute('SELECT * FROM categories').fetchall()

    if request.method == 'POST':
        new_content = request.form['task']
        new_category_id = request.form['category_id']
        conn.execute('UPDATE tasks SET content = ?, category_id = ? WHERE id = ?', (new_content, new_category_id, task_id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

@app.route("/protected")
@requires_auth
def protected():
    return "これは認証されたユーザーだけが見られるページです"


    conn.close()
    return render_template('edit.html', task=task, categories=categories)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
