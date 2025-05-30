import os

tasks = []

# ファイルからタスクを読み込む
def load_tasks():
    if os.path.exists("tasks.txt"):
        with open("tasks.txt", "r", encoding="utf-8") as file:
            for line in file:
                tasks.append(line.strip())

# タスクをファイルに保存する
def save_tasks():
    with open("tasks.txt", "w", encoding="utf-8") as file:
        for task in tasks:
            file.write(task + "\n")

def show_menu():
    print("\n=== ToDoリスト ===")
    print("1. タスクを追加")
    print("2. タスク一覧を表示")
    print("3. タスクを削除")
    print("4. 終了")

load_tasks()

while True:
    show_menu()
    choice = input("選択してください（1〜4）: ")

    if choice == "1":
        task = input("追加するタスクを入力してください: ")
        tasks.append(task)
        save_tasks()
        print(f"タスク「{task}」を追加しました。")

    elif choice == "2":
        if not tasks:
            print("タスクはありません。")
        else:
            print("現在のタスク一覧:")
            for i, task in enumerate(tasks):
                print(f"{i + 1}. {task}")

    elif choice == "3":
        for i, task in enumerate(tasks):
            print(f"{i + 1}. {task}")
        index = int(input("削除するタスクの番号を入力してください: ")) - 1
        if 0 <= index < len(tasks):
            removed = tasks.pop(index)
            save_tasks()
            print(f"タスク「{removed}」を削除しました。")
        else:
            print("無効な番号です。")

    elif choice == "4":
        print("終了します。")
        break

    else:
        print("無効な選択です。")
