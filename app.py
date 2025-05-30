from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta, timezone

# 日本時間（UTC+9）
JST = timezone(timedelta(hours=9))

# 日本時間の現在時刻を取得
now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


app = Flask(__name__)
DB_NAME = "todo.db"

# ✅ カテゴリごとの色設定（関数よりも前に置く）
CATEGORY_COLORS = {
    "仕事": "primary",     # 青
    "買い物": "warning",   # 黄
    "趣味": "success",     # 緑
    "スキル": "info",      # 水色
    "予定": "danger",      # 赤
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
def index():
    keyword = request.args.get("q", "").strip()
    conn = get_db_connection()

    # タスクをカテゴリ名付きで取得
    tasks = conn.execute("""
        SELECT tasks.*, categories.name AS category_name
        FROM tasks LEFT JOIN categories ON tasks.category_id = categories.id
        ORDER BY created_at DESC
    """).fetchall()

    # カテゴリ一覧取得（フォーム用）
    categories = conn.execute("SELECT * FROM categories").fetchall()
    conn.close()

    # 色情報をテンプレートに渡す
    return render_template("index.html", tasks=tasks, categories=categories, keyword=keyword, category_colors=CATEGORY_COLORS)



@app.route("/add", methods=["POST"])
def add():
    task = request.form["task"]
    category_id = request.form.get("category_id")
    if task:
        JST = timezone(timedelta(hours=9))  # 日本時間設定
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
def delete(task_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>")
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

    conn.close()
    return render_template('edit.html', task=task, categories=categories)

# ✅ 起動処理は最後に1回だけ
if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reloader=False)
