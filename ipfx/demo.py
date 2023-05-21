import tkinter as tk
from tkinter import filedialog
import os


root = tk.Tk()
root.withdraw()

selected_folder = filedialog.askdirectory()

file_paths = []

for root_dir, dirs, files in os.walk(selected_folder):
    for file in files:
        if file.lower().endswith('.abf'):
            file_paths.append(os.path.join(root_dir, file))

# 打印文件路径列表
print(len(file_paths))