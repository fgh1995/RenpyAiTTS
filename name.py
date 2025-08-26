import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os


def process_files():
    # 获取用户选择的文件路径
    name_file_path = name_file_entry.get()
    script_file_path = script_file_entry.get()
    output_file_path = output_file_entry.get()

    if not all([name_file_path, script_file_path, output_file_path]):
        messagebox.showerror("错误", "请选择所有必要的文件路径")
        return

    try:
        # 更新进度条和状态
        progress_bar['value'] = 10
        status_label.config(text="正在读取翻译文件...")
        root.update_idletasks()

        # 读取name.rpy文件内容
        with open(name_file_path, 'r', encoding='utf-8') as f:
            name_content = f.read()

        # 提取翻译映射
        progress_bar['value'] = 30
        status_label.config(text="正在提取翻译映射...")
        root.update_idletasks()

        translation_pattern = r'old "([^"]+)"\s+new "([^"]+)"'
        translations = dict(re.findall(translation_pattern, name_content))

        # 读取包含角色定义的.rpy文件
        progress_bar['value'] = 50
        status_label.config(text="正在读取角色定义文件...")
        root.update_idletasks()

        with open(script_file_path, 'r', encoding='utf-8') as f:
            char_content = f.read()

        # 改进的正则表达式，匹配所有Character定义格式
        progress_bar['value'] = 70
        status_label.config(text="正在提取角色定义...")
        root.update_idletasks()

        char_pattern = r'define\s+(\w+)\s*=\s*Character\("([^"]+)"(?:,[^)]+)?\)'
        characters = re.findall(char_pattern, char_content)

        # 创建角色到中文名的映射
        progress_bar['value'] = 80
        status_label.config(text="正在创建翻译映射...")
        root.update_idletasks()

        char_translation = {}
        for var_name, eng_name in characters:
            # 精确匹配大小写
            if eng_name in translations:
                char_translation[var_name] = translations[eng_name]
            else:
                char_translation[var_name] = eng_name  # 如果没有翻译，保持英文原文

        # 生成新的.rpy文件内容 - 使用 x = x 格式
        progress_bar['value'] = 90
        status_label.config(text="正在生成输出文件...")
        root.update_idletasks()

        output_content = "# 角色定义 - 中文版\n\n"
        for var_name, eng_name in characters:
            chinese_name = char_translation[var_name]

            # 直接创建新的定义行，使用 x = x 格式
            if chinese_name == eng_name:
                # 如果没有翻译，保持原格式
                new_line = f'define {var_name} = Character("{eng_name}")'
            else:
                # 如果有翻译，使用中文名
                new_line = f'define {var_name} = Character("{chinese_name}")'

            output_content += new_line + '\n'

        # 写入输出文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        progress_bar['value'] = 100
        status_label.config(text="处理完成！")

        # 显示处理结果
        translated_count = sum(1 for var_name, eng_name in characters if char_translation[var_name] != eng_name)
        result_text = f"处理完成！\n共处理了 {len(characters)} 个角色定义\n{translated_count} 个已翻译，{len(characters) - translated_count} 个保持原文"
        messagebox.showinfo("完成", result_text)

    except Exception as e:
        messagebox.showerror("错误", f"处理文件时发生错误:\n{str(e)}")
        progress_bar['value'] = 0
        status_label.config(text="处理失败")


def browse_name_file():
    filename = filedialog.askopenfilename(title="选择翻译文件 (name.rpy)",
                                          filetypes=[("Ren'Py files", "*.rpy"), ("All files", "*.*")])
    if filename:
        name_file_entry.delete(0, tk.END)
        name_file_entry.insert(0, filename)


def browse_script_file():
    filename = filedialog.askopenfilename(title="选择脚本文件 (script.rpy)",
                                          filetypes=[("Ren'Py files", "*.rpy"), ("All files", "*.*")])
    if filename:
        script_file_entry.delete(0, tk.END)
        script_file_entry.insert(0, filename)


def browse_output_file():
    filename = filedialog.asksaveasfilename(title="保存输出文件", defaultextension=".txt",
                                            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if filename:
        output_file_entry.delete(0, tk.END)
        output_file_entry.insert(0, filename)


# 创建主窗口
root = tk.Tk()
root.title("Ren'Py 角色翻译工具")
root.geometry("600x400")

# 创建框架
main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# 配置网格权重
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

# 翻译文件选择
ttk.Label(main_frame, text="翻译文件 (name.rpy):").grid(row=0, column=0, sticky=tk.W, pady=5)
name_file_entry = ttk.Entry(main_frame, width=50)
name_file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
ttk.Button(main_frame, text="浏览", command=browse_name_file).grid(row=0, column=2, pady=5)

# 脚本文件选择
ttk.Label(main_frame, text="脚本文件 (script.rpy):").grid(row=1, column=0, sticky=tk.W, pady=5)
script_file_entry = ttk.Entry(main_frame, width=50)
script_file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
ttk.Button(main_frame, text="浏览", command=browse_script_file).grid(row=1, column=2, pady=5)

# 输出文件选择
ttk.Label(main_frame, text="输出文件:").grid(row=2, column=0, sticky=tk.W, pady=5)
output_file_entry = ttk.Entry(main_frame, width=50)
output_file_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
ttk.Button(main_frame, text="浏览", command=browse_output_file).grid(row=2, column=2, pady=5)

# 处理按钮
process_button = ttk.Button(main_frame, text="开始处理", command=process_files)
process_button.grid(row=3, column=1, pady=20)

# 进度条
progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
progress_bar.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

# 状态标签
status_label = ttk.Label(main_frame, text="准备就绪")
status_label.grid(row=5, column=0, columnspan=3, pady=5)

# 说明文本
instructions = """
使用说明:
1. 选择翻译文件 (通常是 tl/schinese/base/name.rpy)
2. 选择包含角色定义的脚本文件 (通常是 script.rpy)
3. 选择输出文件路径
4. 点击"开始处理"按钮

处理完成后，输出文件将包含所有角色的中文定义。
"""
ttk.Label(main_frame, text=instructions, justify=tk.LEFT).grid(row=6, column=0, columnspan=3, pady=10, sticky=tk.W)

# 启动主循环
root.mainloop()