import os

folder_path = r"C:\Users\jbc0133\Desktop\python_test"

files = os.listdir(folder_path)

print("フォルダ内のファイル一覧：")
for f in files:
	print(f)
	