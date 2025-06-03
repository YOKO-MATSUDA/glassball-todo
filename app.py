import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, Response
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

# 日本時間
JST = timezone(timedelta(hours=9))

# 環境変数から取得（Renderでは自動で設定される）
DATABASE_URL = os.environ.get("DATABASE_URL")
USERNAME = os.environ.get("BASIC_AUTH_USERNAME")
PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD")

CATEGORY_COLORS = {
    "仕事": "primary",
    "買い物": "warning",
    "趣味": "success",
    "スキル": "info",
    "予定": "danger",
}

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response('認証が必要です。', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                );
            """)
            cur.execute("""
                INSERT INTO categories (name)
                VALUES ('仕事'), ('買い物'), ('趣味'), ('スキル'), ('予定')
                ON CONFLICT DO NOTHING;
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    category_id INTEGER REFERENCES categories(id),
                    created_at TIMESTAMP NOT NULL,
                    is_done BOOLEAN DEFAULT FALSE
                );
            """)
            conn.commit()

    cur.close()
    conn.close()



@app.route("/")
@requires_auth
def index():
    keyword = request.args.get("q", "").strip()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tasks.*, categories.name AS category_name
                FROM tasks LEFT JOIN categories ON tasks.category_id = categories.id
                ORDER BY created_at DESC
            """)
            tasks = cur.fetchall()

            cur.execute("SELECT * FROM categories ORDER BY id")
            categories = cur.fetchall()

    return render_template("index.html", tasks=tasks, categories=categories, keyword=keyword, category_colors=CATEGORY_COLORS)

@app.route("/add", methods=["POST"])
@requires_auth
def add():
    task = request.form["task"]
    category_id = request.form.get("category_id")
    if task:
        now = datetime.now(JST)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tasks (content, created_at, category_id)
                    VALUES (%s, %s, %s)
                """, (task, now, category_id if category_id else None))
                conn.commit()
    return redirect(url_for("index"))

@app.route("/delete/<int:task_id>")
@requires_auth
def delete(task_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>")
@requires_auth
def toggle(task_id):
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT is_done FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()
            if task:
                new_status = not task['is_done']
                cur.execute("UPDATE tasks SET is_done = %s WHERE id = %s", (new_status, task_id))
                conn.commit()
    return redirect(url_for("index"))

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@requires_auth
def edit(task_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if request.method == "POST":
                new_content = request.form["task"]
                new_category_id = request.form["category_id"]
                cur.execute("""
                    UPDATE tasks SET content = %s, category_id = %s WHERE id = %s
                """, (new_content, new_category_id, task_id))
                conn.commit()
                return redirect(url_for("index"))

            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            task = cur.fetchone()
            cur.execute("SELECT * FROM categories ORDER BY id")
            categories = cur.fetchall()

    return render_template("edit.html", task=task, categories=categories)

@app.route("/protected")
@requires_auth
def protected():
    return "これは認証されたユーザーだけが見られるページです"

# if __name__ == "__main__":

#     app.run(debug=True, use_reloader=False)  # init_db() は削除（別スクリプト化推奨）

if __name__ == "__main__":
    init_db()  # ← この行を一時的に追加
    app.run(debug=True, use_reloader=False)

