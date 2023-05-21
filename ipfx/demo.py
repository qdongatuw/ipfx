from tkinter import filedialog
import os

# 创建一个Tkinter窗口


# 弹出文件选择对话框，允许选择多个文件或文件夹
selected_paths = filedialog.askopenfilenames()

# 创建一个空的文件路径列表
file_paths = []

# 遍历选中的路径
for path in selected_paths:
    if os.path.isfile(path) and path.lower().endswith('.abf'):
        # 如果路径是文件且扩展名为.abf，则直接将其添加到文件路径列表中
        file_paths.append(path)
    elif os.path.isdir(path):
        # 如果路径是文件夹，则使用os.walk遍历文件夹及子文件夹下的所有.abf文件
        for root_dir, dirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith('.abf'):
                    file_paths.append(os.path.join(root_dir, file))
print(file_paths)