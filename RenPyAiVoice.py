import os
import re
import base64
import hashlib
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests

# 设置Tcl/Tk库路径
tcl_library_path = "C:/Users/Administrator/AppData/Local/Programs/Python/Python313/tcl/tcl8.6"
tk_library_path = "C:/Users/Administrator/AppData/Local/Programs/Python/Python313/tcl/tk8.6"

if os.path.exists(tcl_library_path):
    os.environ["TCL_LIBRARY"] = tcl_library_path
if os.path.exists(tk_library_path):
    os.environ["TK_LIBRARY"] = tk_library_path


class TTSGeneratorTool:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS语音合成工具 - 三步流程")
        self.root.geometry("950x800")

        # 创建选项卡控件
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建三个选项卡（按顺序）
        self.tab1 = ttk.Frame(self.notebook)  # 角色定义提取
        self.tab2 = ttk.Frame(self.notebook)  # 对话文本提取
        self.tab3 = ttk.Frame(self.notebook)  # 语音合成

        self.notebook.add(self.tab1, text='1. 角色定义提取和翻译')
        self.notebook.add(self.tab2, text='2. 对话文本提取')
        self.notebook.add(self.tab3, text='3. 语音合成')

        # 初始化各个选项卡的UI
        self.setup_tab1_ui()
        self.setup_tab2_ui()
        self.setup_tab3_ui()

        # 初始化TTS生成器
        self.tts_generator = TTSGenerator()

        # 存储中间结果
        self.translation_dict = {}
        self.character_stats = {}

    def setup_tab1_ui(self):
        """设置角色定义提取选项卡的UI"""
        # 主框架
        main_frame = ttk.Frame(self.tab1, padding="10")
        main_frame.pack(fill='both', expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="第一步：角色定义提取和翻译", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # 名称.rpy文件选择
        ttk.Label(main_frame, text="name.rpy文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_rpy_path = tk.StringVar()
        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(name_frame, textvariable=self.name_rpy_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(name_frame, text="浏览", command=self.browse_name_rpy).pack(side=tk.RIGHT, padx=(5, 0))

        # 脚本.rpy文件选择
        ttk.Label(main_frame, text="script.rpy文件:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.script_rpy_path = tk.StringVar()
        script_frame = ttk.Frame(main_frame)
        script_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(script_frame, textvariable=self.script_rpy_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(script_frame, text="浏览", command=self.browse_script_rpy).pack(side=tk.RIGHT, padx=(5, 0))

        # 输出文件路径
        ttk.Label(main_frame, text="输出文件:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.output_translation_path = tk.StringVar(value="角色定义中文版.txt")
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(output_frame, textvariable=self.output_translation_path, width=60).pack(side=tk.LEFT, fill=tk.X,
                                                                                          expand=True)
        ttk.Button(output_frame, text="浏览", command=self.browse_output_translation).pack(side=tk.RIGHT, padx=(5, 0))

        # 执行按钮
        self.extract_button = ttk.Button(main_frame, text="提取角色定义", command=self.extract_character_definitions)
        self.extract_button.grid(row=4, column=1, pady=15)

        # 状态显示
        self.tab1_status = tk.StringVar(value="准备就绪")
        ttk.Label(main_frame, textvariable=self.tab1_status).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)

        # 结果显示区域
        ttk.Label(main_frame, text="提取结果:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.tab1_result = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.tab1_result.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def setup_tab2_ui(self):
        """设置对话文本提取选项卡的UI"""
        # 主框架
        main_frame = ttk.Frame(self.tab2, padding="10")
        main_frame.pack(fill='both', expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="第二步：对话文本提取", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # 角色定义文件选择
        ttk.Label(main_frame, text="角色定义文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.character_def_path = tk.StringVar()
        char_frame = ttk.Frame(main_frame)
        char_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(char_frame, textvariable=self.character_def_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(char_frame, text="浏览", command=self.browse_character_def).pack(side=tk.RIGHT, padx=(5, 0))

        # 脚本文件夹选择
        ttk.Label(main_frame, text="脚本文件夹:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.scripts_folder_path = tk.StringVar()
        scripts_frame = ttk.Frame(main_frame)
        scripts_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(scripts_frame, textvariable=self.scripts_folder_path, width=60).pack(side=tk.LEFT, fill=tk.X,
                                                                                       expand=True)
        ttk.Button(scripts_frame, text="浏览", command=self.browse_scripts_folder).pack(side=tk.RIGHT, padx=(5, 0))

        # 输出文件夹
        ttk.Label(main_frame, text="输出文件夹:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.dialogue_output_path = tk.StringVar(value="对话提取结果")
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(output_frame, textvariable=self.dialogue_output_path, width=60).pack(side=tk.LEFT, fill=tk.X,
                                                                                       expand=True)
        ttk.Button(output_frame, text="浏览", command=self.browse_dialogue_output).pack(side=tk.RIGHT, padx=(5, 0))

        # 执行按钮
        self.extract_dialogue_button = ttk.Button(main_frame, text="提取对话文本", command=self.extract_dialogues)
        self.extract_dialogue_button.grid(row=4, column=1, pady=15)

        # 状态显示
        self.tab2_status = tk.StringVar(value="准备就绪")
        ttk.Label(main_frame, textvariable=self.tab2_status).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=5)

        # 结果显示区域
        ttk.Label(main_frame, text="提取统计:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.tab2_result = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.tab2_result.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def setup_tab3_ui(self):
        """设置语音合成选项卡的UI"""
        # 主框架
        main_frame = ttk.Frame(self.tab3, padding="10")
        main_frame.pack(fill='both', expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="第三步：语音合成", font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))

        # 输入文件选择
        ttk.Label(main_frame, text="输入文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.input_path = tk.StringVar()
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(input_frame, textvariable=self.input_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览", command=self.browse_input).pack(side=tk.RIGHT, padx=(5, 0))

        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_path = tk.StringVar(value="tts_output")
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(output_frame, textvariable=self.output_path, width=60).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览", command=self.browse_output).pack(side=tk.RIGHT, padx=(5, 0))

        # 模型选择
        ttk.Label(main_frame, text="模型:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="原神-中文-莱欧斯利_ZH")
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, width=57)
        model_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        model_combo['values'] = ("原神-中文-莱欧斯利_ZH", "其他模型1", "其他模型2")

        # 语速设置
        ttk.Label(main_frame, text="语速因子:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(main_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, textvariable=self.speed_var).grid(row=4, column=2, sticky=tk.W, padx=(5, 0), pady=5)

        # 线程数设置
        ttk.Label(main_frame, text="线程数:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.thread_count_var = tk.IntVar(value=3)
        thread_spinbox = ttk.Spinbox(main_frame, from_=1, to=10, textvariable=self.thread_count_var, width=10)
        thread_spinbox.grid(row=5, column=1, sticky=tk.W, pady=5)

        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始合成", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 进度条
        ttk.Label(main_frame, text="进度:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=5)

        # 状态标签
        self.tab3_status = tk.StringVar(value="准备就绪")
        ttk.Label(main_frame, textvariable=self.tab3_status).grid(row=8, column=0, columnspan=3, sticky=tk.W, pady=5)

        # 统计信息
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(stats_frame, text="成功:").pack(side=tk.LEFT)
        self.success_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.success_var).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(stats_frame, text="失败:").pack(side=tk.LEFT)
        self.failed_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.failed_var).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(stats_frame, text="跳过:").pack(side=tk.LEFT)
        self.skipped_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.skipped_var).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(stats_frame, text="总计:").pack(side=tk.LEFT)
        self.total_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.total_var).pack(side=tk.LEFT)

        ttk.Label(stats_frame, text="活动线程:").pack(side=tk.LEFT, padx=(20, 0))
        self.active_threads_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.active_threads_var).pack(side=tk.LEFT)

        # 日志输出
        ttk.Label(main_frame, text="日志:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(11, weight=1)

        # 多线程相关变量
        self.is_processing = False
        self.stop_requested = False
        self.task_queue = queue.Queue()
        self.threads = []
        self.processed_count = 0
        self.lock = threading.Lock()

    # Tab 1: 角色定义提取相关方法
    def browse_name_rpy(self):
        filename = filedialog.askopenfilename(
            title="选择name.rpy文件",
            filetypes=[("Ren'Py文件", "*.rpy"), ("所有文件", "*.*")]
        )
        if filename:
            self.name_rpy_path.set(filename)

    def browse_script_rpy(self):
        filename = filedialog.askopenfilename(
            title="选择script.rpy文件",
            filetypes=[("Ren'Py文件", "*.rpy"), ("所有文件", "*.*")]
        )
        if filename:
            self.script_rpy_path.set(filename)

    def browse_output_translation(self):
        filename = filedialog.asksaveasfilename(
            title="保存角色定义文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_translation_path.set(filename)

    def extract_character_definitions(self):
        """提取角色定义"""
        if not self.name_rpy_path.get() or not self.script_rpy_path.get():
            messagebox.showerror("错误", "请选择name.rpy和script.rpy文件")
            return

        try:
            self.tab1_status.set("正在提取角色定义...")

            # 读取name.rpy文件内容
            with open(self.name_rpy_path.get(), 'r', encoding='utf-8') as f:
                name_content = f.read()

            # 提取翻译映射
            translation_pattern = r'old "([^"]+)"\s+new "([^"]+)"'
            translations = dict(re.findall(translation_pattern, name_content))

            # 读取包含角色定义的.rpy文件
            with open(self.script_rpy_path.get(), 'r', encoding='utf-8') as f:
                char_content = f.read()

            # 改进的正则表达式，匹配所有Character定义格式
            char_pattern = r'define\s+(\w+)\s*=\s*Character\("([^"]+)"(?:,[^)]+)?\)'
            characters = re.findall(char_pattern, char_content)

            # 创建角色到中文名的映射
            char_translation = {}
            for var_name, eng_name in characters:
                if eng_name in translations:
                    char_translation[var_name] = translations[eng_name]
                else:
                    char_translation[var_name] = eng_name

            # 生成输出内容
            output_content = "# 角色定义 - 中文版\n\n"
            for var_name, eng_name in characters:
                chinese_name = char_translation[var_name]
                if chinese_name == eng_name:
                    new_line = f'{var_name} = {eng_name}'
                else:
                    new_line = f'{var_name} = {chinese_name}'
                output_content += new_line + '\n'

            # 写入输出文件
            with open(self.output_translation_path.get(), 'w', encoding='utf-8') as f:
                f.write(output_content)

            # 显示结果
            self.tab1_result.delete(1.0, tk.END)
            self.tab1_result.insert(tk.END, f"找到 {len(characters)} 个角色定义:\n\n")

            translated_count = 0
            for var_name, eng_name in characters:
                chinese_name = char_translation[var_name]
                status = "✓ 已翻译" if chinese_name != eng_name else "✗ 保持原文"
                self.tab1_result.insert(tk.END, f"{var_name} = {eng_name} -> {chinese_name} ({status})\n")
                if chinese_name != eng_name:
                    translated_count += 1

            self.tab1_result.insert(tk.END,
                                    f"\n翻译统计：{translated_count} 个已翻译，{len(characters) - translated_count} 个保持原文")
            self.tab1_status.set(f"提取完成！共处理了 {len(characters)} 个角色定义")

            # 保存翻译字典供后续使用
            self.translation_dict = char_translation

        except Exception as e:
            self.tab1_status.set(f"提取失败: {str(e)}")
            messagebox.showerror("错误", f"提取角色定义时出错: {str(e)}")

    # Tab 2: 对话文本提取相关方法
    def browse_character_def(self):
        filename = filedialog.askopenfilename(
            title="选择角色定义文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.character_def_path.set(filename)

    def browse_scripts_folder(self):
        directory = filedialog.askdirectory(title="选择脚本文件夹")
        if directory:
            self.scripts_folder_path.set(directory)

    def browse_dialogue_output(self):
        directory = filedialog.askdirectory(title="选择输出文件夹")
        if directory:
            self.dialogue_output_path.set(directory)

    def load_character_translations_from_file(self, file_path):
        """从文件中加载角色代码到中文名称的映射"""
        translation_dict = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                pattern = r'^([A-Za-z0-9_]+)\s*=\s*(.+)$'
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(pattern, line)
                        if match:
                            character_code = match.group(1)
                            chinese_name = match.group(2).strip()
                            translation_dict[character_code] = chinese_name
        except Exception as e:
            raise Exception(f"读取角色定义文件时出错: {e}")
        return translation_dict

    def extract_text_from_rpy(self, file_path, translation_dict):
        """从.rpy文件中提取角色对话和旁白文本"""
        dialogue_pattern = r'^([A-Za-z_]+) "([^"]*)"'
        narration_pattern = r'^"([^"]*)"'

        exclude_patterns = [
            r'^old "', r'^#', r'^translate ', r'^label ',
            r'^menu', r'^jump ', r'^return', r'^python', r'^$'
        ]

        dialogues = []
        narrations = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if any(re.match(pattern, line) for pattern in exclude_patterns):
                        continue

                    dialogue_match = re.match(dialogue_pattern, line)
                    if dialogue_match:
                        character_code = dialogue_match.group(1)
                        dialogue_text = dialogue_match.group(2)
                        cleaned_text = re.sub(r'\{[^}]*\}', '', dialogue_text)
                        if cleaned_text.strip():
                            character_name = translation_dict.get(character_code, character_code)
                            dialogues.append((character_name, cleaned_text.strip()))
                        continue

                    narration_match = re.match(narration_pattern, line)
                    if narration_match:
                        narration_text = narration_match.group(1)
                        cleaned_text = re.sub(r'\{[^}]*\}', '', narration_text)
                        if cleaned_text.strip():
                            narrations.append(cleaned_text.strip())
        except Exception as e:
            raise Exception(f"处理文件 {file_path} 时出错: {e}")

        return {"dialogues": dialogues, "narrations": narrations}

    def extract_dialogues(self):
        """提取对话文本"""
        if not self.character_def_path.get() or not self.scripts_folder_path.get():
            messagebox.showerror("错误", "请选择角色定义文件和脚本文件夹")
            return

        try:
            self.tab2_status.set("正在提取对话文本...")

            # 加载角色翻译
            translation_dict = self.load_character_translations_from_file(self.character_def_path.get())

            all_dialogues = []
            all_narrations = []

            # 遍历文件夹中的所有.rpy文件
            for root, dirs, files in os.walk(self.scripts_folder_path.get()):
                for file in files:
                    if file.endswith('.rpy'):
                        file_path = os.path.join(root, file)
                        result = self.extract_text_from_rpy(file_path, translation_dict)
                        all_dialogues.extend(result["dialogues"])
                        all_narrations.extend(result["narrations"])

            # 保存旁白到文件
            narration_file = os.path.join(self.dialogue_output_path.get(), '旁白.txt')
            os.makedirs(os.path.dirname(narration_file), exist_ok=True)
            with open(narration_file, 'w', encoding='utf-8') as f:
                for narration in all_narrations:
                    f.write(f"None:{narration}\n")

            # 按角色分类统计
            character_stats = {}
            for character, dialogue in all_dialogues:
                if character not in character_stats:
                    character_stats[character] = []
                character_stats[character].append(dialogue)

            # 保存按角色分类的对话
            for character, lines in character_stats.items():
                safe_filename = re.sub(r'[\\/*?:"<>|]', '_', character)
                char_file = os.path.join(self.dialogue_output_path.get(), f'dialogue_{safe_filename}.txt')
                with open(char_file, 'w', encoding='utf-8') as f:
                    for dialogue in lines:
                        f.write(f"{character}:{dialogue}\n")

            # 显示统计结果
            self.tab2_result.delete(1.0, tk.END)
            self.tab2_result.insert(tk.END, f"提取完成！\n\n")
            self.tab2_result.insert(tk.END, f"总对话条数: {len(all_dialogues)}\n")
            self.tab2_result.insert(tk.END, f"总旁白条数: {len(all_narrations)}\n")
            self.tab2_result.insert(tk.END, f"角色数量: {len(character_stats)}\n\n")
            self.tab2_result.insert(tk.END, f"角色对话统计:\n")

            for character, lines in character_stats.items():
                self.tab2_result.insert(tk.END, f"  {character}: {len(lines)} 条\n")

            self.tab2_result.insert(tk.END, f"\n结果已保存到: {self.dialogue_output_path.get()}")
            self.tab2_status.set("对话提取完成！")

            # 保存统计信息供后续使用
            self.character_stats = character_stats

        except Exception as e:
            self.tab2_status.set(f"提取失败: {str(e)}")
            messagebox.showerror("错误", f"提取对话文本时出错: {str(e)}")

    # Tab 3: 语音合成相关方法
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="选择输入文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_path.set(filename)

    def browse_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_path.set(directory)

    def log_message(self, message):
        """向日志区域添加消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_active_threads(self):
        """更新活动线程计数"""
        active_count = sum(1 for thread in self.threads if thread.is_alive())
        self.active_threads_var.set(str(active_count))

    def worker_thread(self, thread_id):
        """工作线程函数"""
        while not self.stop_requested:
            try:
                task = self.task_queue.get(timeout=1)
                i, original_line, total_lines, output_dir, model_name, speed_factor = task

                if self.stop_requested:
                    break

                processed_line = re.sub(r'^[^:]+:\s*', '', original_line.strip())

                if not processed_line:
                    with self.lock:
                        self.skipped_var.set(str(int(self.skipped_var.get()) + 1))
                    continue

                # 生成SHA1哈希文件名
                sha1_hash = hashlib.sha1()
                sha1_hash.update(original_line.encode('utf-8'))
                filename = sha1_hash.hexdigest() + ".wav"
                output_path = os.path.join(output_dir, filename)

                # 检查文件是否已存在
                if os.path.exists(output_path):
                    with self.lock:
                        self.log_message(f"⏭️ 线程{thread_id}: 跳过已存在文件: {filename}")
                        self.skipped_var.set(str(int(self.skipped_var.get()) + 1))
                    continue

                # 生成TTS
                with self.lock:
                    self.log_message(f"🧵 线程{thread_id}: [{i + 1}/{total_lines}] 处理: {processed_line[:50]}...")

                if self.tts_generator.generate_tts(processed_line, output_path, model_name, speed_factor):
                    with self.lock:
                        self.success_var.set(str(int(self.success_var.get()) + 1))
                        self.log_message(f"✅ 线程{thread_id}: 成功生成: {filename}")
                else:
                    with self.lock:
                        self.failed_var.set(str(int(self.failed_var.get()) + 1))
                        self.log_message(f"❌ 线程{thread_id}: 生成失败: {filename}")

                # 更新进度
                with self.lock:
                    self.processed_count += 1
                    progress = (self.processed_count / total_lines) * 100
                    self.progress_var.set(progress)
                    self.tab3_status.set(f"处理中: {self.processed_count}/{total_lines}")

                self.task_queue.task_done()
                self.update_active_threads()
                time.sleep(0.5)

            except queue.Empty:
                break
            except Exception as e:
                with self.lock:
                    self.failed_var.set(str(int(self.failed_var.get()) + 1))
                    self.log_message(f"❌ 线程{thread_id}: 发生错误: {str(e)}")
                self.task_queue.task_done()

    def start_processing(self):
        if not self.input_path.get():
            messagebox.showerror("错误", "请选择输入文件")
            return

        if not os.path.exists(self.input_path.get()):
            messagebox.showerror("错误", "输入文件不存在")
            return

        # 重置状态
        self.is_processing = True
        self.stop_requested = False
        self.processed_count = 0
        self.success_var.set("0")
        self.failed_var.set("0")
        self.skipped_var.set("0")
        self.total_var.set("0")
        self.progress_var.set(0)
        self.active_threads_var.set("0")
        self.log_text.delete(1.0, tk.END)

        # 清空任务队列
        while not self.task_queue.empty():
            self.task_queue.get_nowait()

        # 更新UI状态
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        self.tab3_status.set("正在准备...")

        # 在新线程中处理
        thread = threading.Thread(target=self.prepare_and_process)
        thread.daemon = True
        thread.start()

    def prepare_and_process(self):
        try:
            input_file = self.input_path.get()
            output_dir = self.output_path.get()
            model_name = self.model_var.get()
            speed_factor = self.speed_var.get()
            thread_count = self.thread_count_var.get()

            # 读取文件
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)
            self.total_var.set(str(total_lines))

            # 填充任务队列
            for i, line in enumerate(lines):
                original_line = line.strip()
                if original_line:
                    self.task_queue.put((i, original_line, total_lines, output_dir, model_name, speed_factor))

            self.log_message(f"开始处理 {total_lines} 条对话，使用 {thread_count} 个线程")
            self.log_message(f"输出目录: {output_dir}")
            self.log_message("-" * 50)

            # 创建工作线程
            self.threads = []
            for i in range(thread_count):
                thread = threading.Thread(target=self.worker_thread, args=(i + 1,))
                thread.daemon = True
                thread.start()
                self.threads.append(thread)

            # 等待所有任务完成
            self.task_queue.join()

            # 检查是否被用户停止
            if not self.stop_requested:
                self.tab3_status.set("处理完成")
                self.log_message("\n" + "=" * 50)
                self.log_message("处理完成!")
                self.log_message(f"成功: {self.success_var.get()}")
                self.log_message(f"失败: {self.failed_var.get()}")
                self.log_message(f"跳过: {self.skipped_var.get()}")
                self.log_message(f"总计: {total_lines}")

        except Exception as e:
            self.log_message(f"处理过程中出错: {str(e)}")
            self.tab3_status.set("处理出错")
        finally:
            # 恢复UI状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_processing = False
            self.stop_requested = False

    def stop_processing(self):
        self.stop_requested = True
        self.tab3_status.set("正在停止...")
        self.log_message("正在停止所有线程...")

        # 清空任务队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except:
                pass


class TTSGenerator:
    def __init__(self):
        self.headers = {
            "Connection": "keep-alive",
            "sec-ch-ua": "\"Chromium\";v=\"92\", \" Not A;Brand\";v=\"99\", \"Microsoft Edge\";v=\"92\"",
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua-mobile": "?0",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.67",
            "Content-Type": "application/json",
            "Origin": "http://127.0.0.1:8000",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "http://127.0.0.1:8000/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
        }

    def generate_tts(self, text, output_path, model_name="原神-中文-莱欧斯利_ZH", speed_factor=1.0):
        """生成单个文本的TTS"""
        url = "http://127.0.0.1:8000/infer_single"

        data = {
            "dl_url": "http://127.0.0.1:8000",
            "version": "v4",
            "model_name": model_name,
            "prompt_text_lang": "中文",
            "emotion": "默认",
            "text": text,
            "text_lang": "中文",
            "top_k": 10,
            "top_p": 1,
            "temperature": 1,
            "text_split_method": "按标点符号切",
            "batch_size": 10,
            "batch_threshold": 0.75,
            "split_bucket": True,
            "speed_facter": speed_factor,
            "fragment_interval": 0.3,
            "media_type": "wav",
            "parallel_infer": True,
            "repetition_penalty": 1.35,
            "seed": 473410238,
            "sample_steps": 16,
            "if_sr": False
        }

        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if result.get("msg") == "合成成功":
                    audio_url = result.get("audio_url")
                    audio_response = requests.get(audio_url, timeout=60)
                    if audio_response.status_code == 200:
                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(audio_response.content)
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

        except Exception as e:
            return False


def main():
    # 设置Tcl/Tk库路径
    try:
        python_dir = os.path.dirname(os.__file__)
        tcl_dir = os.path.join(python_dir, "tcl")
        if os.path.exists(tcl_dir):
            os.environ["TCL_LIBRARY"] = os.path.join(tcl_dir, "tcl8.6")
            os.environ["TK_LIBRARY"] = os.path.join(tcl_dir, "tk8.6")
    except:
        pass

    root = tk.Tk()
    app = TTSGeneratorTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()