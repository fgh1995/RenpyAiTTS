# 设置Tcl/Tk库路径（根据你的实际安装路径调整）
import base64
import re
import hashlib  # 添加hashlib用于生成SHA1哈希
import queue  # 添加队列用于多线程处理
import os
import requests
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 尝试自动设置Tcl/Tk路径
try:
    python_dir = os.path.dirname(os.__file__)
    tcl_dir = os.path.join(python_dir, "tcl")
    if os.path.exists(tcl_dir):
        os.environ["TCL_LIBRARY"] = os.path.join(tcl_dir, "tcl8.6")
        os.environ["TK_LIBRARY"] = os.path.join(tcl_dir, "tk8.6")
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


class DialogueExtractor:
    @staticmethod
    def load_character_translations_from_file(file_path):
        """
        从文件中加载角色代码到中文名称的映射

        Args:
            file_path (str): 角色定义文件的路径

        Returns:
            dict: 角色代码到中文名称的映射字典
        """
        translation_dict = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 使用正则表达式提取角色定义
                pattern = r'^([A-Za-z0-9_]+)\s*=\s*(.+)$'

                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # 跳过空行和注释
                        match = re.match(pattern, line)
                        if match:
                            character_code = match.group(1)
                            chinese_name = match.group(2).strip()
                            translation_dict[character_code] = chinese_name

            return translation_dict

        except Exception as e:
            raise Exception(f"读取角色定义文件时出错: {e}")

    @staticmethod
    def extract_text_from_rpy(file_path, translation_dict):
        """
        从.rpy文件中提取角色对话（包含角色代码）和旁白文本

        Args:
            file_path (str): .rpy文件的路径
            translation_dict (dict): 角色代码到中文名称的映射字典

        Returns:
            dict: 包含提取的对话（带角色中文名）和旁白的字典
        """
        # 正则表达式模式
        dialogue_pattern = r'^([A-Za-z_]+) "([^"]*)"'  # 角色对话模式，捕获角色代码和文本
        narration_pattern = r'^"([^"]*)"'  # 旁白模式

        # 排除模式 - 不需要的内容
        exclude_patterns = [
            r'^old "',  # 菜单选项
            r'^#',  # 注释
            r'^translate ',  # 翻译标签
            r'^label ',  # 标签
            r'^menu',  # 菜单
            r'^jump ',  # 跳转
            r'^return',  # 返回
            r'^python',  # Python代码
            r'^$'  # 空行
        ]

        dialogues = []  # 格式: (角色中文名, 文本)
        narrations = []  # 格式: 文本

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()

                    # 检查是否需要排除
                    if any(re.match(pattern, line) for pattern in exclude_patterns):
                        continue

                    # 检查是否为角色对话
                    dialogue_match = re.match(dialogue_pattern, line)
                    if dialogue_match:
                        character_code = dialogue_match.group(1)
                        dialogue_text = dialogue_match.group(2)
                        # 移除{}标签
                        cleaned_text = re.sub(r'\{[^}]*\}', '', dialogue_text)
                        if cleaned_text.strip():  # 确保不是空字符串
                            # 将角色代码转换为中文名称
                            character_name = translation_dict.get(character_code, character_code)
                            dialogues.append((character_name, cleaned_text.strip()))
                        continue

                    # 检查是否为旁白
                    narration_match = re.match(narration_pattern, line)
                    if narration_match:
                        narration_text = narration_match.group(1)
                        # 移除{}标签
                        cleaned_text = re.sub(r'\{[^}]*\}', '', narration_text)
                        if cleaned_text.strip():  # 确保不是空字符串
                            narrations.append(cleaned_text.strip())

        except Exception as e:
            raise Exception(f"处理文件 {file_path} 时出错: {e}")

        return {
            "dialogues": dialogues,
            "narrations": narrations
        }

    @staticmethod
    def process_rpy_files(folder_path, translation_file_path, output_path):
        """
        处理文件夹中的所有.rpy文件

        Args:
            folder_path (str): 文件夹路径
            translation_file_path (str): 角色定义文件路径
            output_path (str): 输出目录路径
        """
        # 加载角色翻译
        translation_dict = DialogueExtractor.load_character_translations_from_file(translation_file_path)

        all_dialogues = []  # 格式: (角色中文名, 文本)
        all_narrations = []  # 格式: 文本

        # 遍历文件夹中的所有文件
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.rpy'):
                    file_path = os.path.join(root, file)

                    # 提取文本
                    result = DialogueExtractor.extract_text_from_rpy(file_path, translation_dict)
                    all_dialogues.extend(result["dialogues"])
                    all_narrations.extend(result["narrations"])

        # 保存旁白到文件
        narration_file = os.path.join(output_path, '旁白.txt')
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
            # 创建安全的文件名
            safe_filename = re.sub(r'[\\/*?:"<>|]', '_', character)
            char_file = os.path.join(output_path, f'dialogue_{safe_filename}.txt')
            with open(char_file, 'w', encoding='utf-8') as f:
                for dialogue in lines:
                    f.write(f"{character}:{dialogue}\n")
        invalid_chars_pattern = r"[\\/*?:\"<>|]"

        return {
            "dialogues_count": len(all_dialogues),
            "narrations_count": len(all_narrations),
            "characters_count": len(character_stats),
            "narration_file": narration_file,
            "character_files": [os.path.join(output_path, f'dialogue_{re.sub(invalid_chars_pattern, "_", char)}.txt')
                                for char in character_stats.keys()]
        }


class TTSGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS语音合成与对话提取工具")
        self.root.geometry("800x700")

        self.tts_generator = TTSGenerator()
        self.dialogue_extractor = DialogueExtractor()
        self.is_processing = False
        self.stop_requested = False
        self.task_queue = queue.Queue()
        self.threads = []
        self.processed_count = 0
        self.lock = threading.Lock()

        self.setup_ui()

    def setup_ui(self):
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # 创建TTS合成选项卡
        self.tts_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tts_frame, text="TTS语音合成")

        # 创建对话提取选项卡
        self.extract_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.extract_frame, text="对话提取")

        # 设置TTS合成界面
        self.setup_tts_tab()

        # 设置对话提取界面
        self.setup_extract_tab()

    def setup_tts_tab(self):
        # 输入文件选择
        ttk.Label(self.tts_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path = tk.StringVar()
        input_frame = ttk.Frame(self.tts_frame)
        input_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览", command=self.browse_tts_input).pack(side=tk.RIGHT, padx=(5, 0))

        # 输出目录选择
        ttk.Label(self.tts_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_path = tk.StringVar(value="C:/Users/Administrator/Desktop/tts_output")
        output_frame = ttk.Frame(self.tts_frame)
        output_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览", command=self.browse_tts_output).pack(side=tk.RIGHT, padx=(5, 0))

        # 模型选择
        ttk.Label(self.tts_frame, text="模型:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.model_var = tk.StringVar(value="原神-中文-莱欧斯利_ZH")
        model_combo = ttk.Combobox(self.tts_frame, textvariable=self.model_var, width=50)
        model_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        model_combo['values'] = ("原神-中文-莱欧斯利_ZH", "其他模型1", "其他模型2")

        # 语速设置
        ttk.Label(self.tts_frame, text="语速因子:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(self.tts_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(self.tts_frame, textvariable=self.speed_var).grid(row=3, column=2, sticky=tk.W, padx=(5, 0), pady=5)

        # 线程数设置
        ttk.Label(self.tts_frame, text="线程数:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.thread_count_var = tk.IntVar(value=3)
        thread_spinbox = ttk.Spinbox(self.tts_frame, from_=1, to=10, textvariable=self.thread_count_var, width=10)
        thread_spinbox.grid(row=4, column=1, sticky=tk.W, pady=5)

        # 控制按钮框架
        button_frame = ttk.Frame(self.tts_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始合成", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 进度条
        ttk.Label(self.tts_frame, text="进度:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.tts_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)

        # 状态标签
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(self.tts_frame, textvariable=self.status_var)
        status_label.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=5)

        # 统计信息
        stats_frame = ttk.Frame(self.tts_frame)
        stats_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

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

        # 活动线程显示
        ttk.Label(stats_frame, text="活动线程:").pack(side=tk.LEFT, padx=(20, 0))
        self.active_threads_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, textvariable=self.active_threads_var).pack(side=tk.LEFT)

        # 日志输出
        ttk.Label(self.tts_frame, text="日志:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.log_text = scrolledtext.ScrolledText(self.tts_frame, height=15, width=70)
        self.log_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        self.tts_frame.columnconfigure(1, weight=1)
        self.tts_frame.rowconfigure(10, weight=1)

    def setup_extract_tab(self):
        # RPY文件夹选择
        ttk.Label(self.extract_frame, text="RPY文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.rpy_folder_path = tk.StringVar()
        rpy_frame = ttk.Frame(self.extract_frame)
        rpy_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(rpy_frame, textvariable=self.rpy_folder_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(rpy_frame, text="浏览", command=self.browse_rpy_folder).pack(side=tk.RIGHT, padx=(5, 0))

        # 角色定义文件选择
        ttk.Label(self.extract_frame, text="角色定义文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.character_file_path = tk.StringVar()
        char_frame = ttk.Frame(self.extract_frame)
        char_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(char_frame, textvariable=self.character_file_path, width=50).pack(side=tk.LEFT, fill=tk.X,
                                                                                    expand=True)
        ttk.Button(char_frame, text="浏览", command=self.browse_character_file).pack(side=tk.RIGHT, padx=(5, 0))

        # 输出目录选择
        ttk.Label(self.extract_frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.extract_output_path = tk.StringVar(value="C:/Users/Administrator/Desktop/extracted_dialogues")
        extract_output_frame = ttk.Frame(self.extract_frame)
        extract_output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(extract_output_frame, textvariable=self.extract_output_path, width=50).pack(side=tk.LEFT, fill=tk.X,
                                                                                              expand=True)
        ttk.Button(extract_output_frame, text="浏览", command=self.browse_extract_output).pack(side=tk.RIGHT,
                                                                                               padx=(5, 0))

        # 提取按钮
        self.extract_button = ttk.Button(self.extract_frame, text="提取对话", command=self.extract_dialogues)
        self.extract_button.grid(row=3, column=0, columnspan=3, pady=10)

        # 提取结果显示
        ttk.Label(self.extract_frame, text="提取结果:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.extract_result_text = scrolledtext.ScrolledText(self.extract_frame, height=20, width=70)
        self.extract_result_text.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # 配置网格权重
        self.extract_frame.columnconfigure(1, weight=1)
        self.extract_frame.rowconfigure(5, weight=1)

    def browse_tts_input(self):
        filename = filedialog.askopenfilename(
            title="选择输入文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_path.set(filename)

    def browse_tts_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_path.set(directory)

    def browse_rpy_folder(self):
        directory = filedialog.askdirectory(title="选择RPY文件夹")
        if directory:
            self.rpy_folder_path.set(directory)

    def browse_character_file(self):
        filename = filedialog.askopenfilename(
            title="选择角色定义文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.character_file_path.set(filename)

    def browse_extract_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.extract_output_path.set(directory)

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
                # 从队列中获取任务，设置超时时间
                task = self.task_queue.get(timeout=1)
                i, original_line, total_lines, output_dir, model_name, speed_factor = task

                if self.stop_requested:
                    break

                # 处理行
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
                    self.status_var.set(f"处理中: {self.processed_count}/{total_lines}")

                # 标记任务完成
                self.task_queue.task_done()

                # 更新活动线程计数
                self.update_active_threads()

                # 添加短暂延迟以避免服务器过载
                time.sleep(0.5)

            except queue.Empty:
                # 队列为空，退出线程
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
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("正在准备...")

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
                if original_line:  # 只添加非空行
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
                self.status_var.set("处理完成")
                self.log_message("\n" + "=" * 50)
                self.log_message("处理完成!")
                self.log_message(f"成功: {self.success_var.get()}")
                self.log_message(f"失败: {self.failed_var.get()}")
                self.log_message(f"跳过: {self.skipped_var.get()}")
                self.log_message(f"总计: {total_lines}")

        except Exception as e:
            self.log_message(f"处理过程中出错: {str(e)}")
            self.status_var.set("处理出错")
        finally:
            # 恢复UI状态
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.is_processing = False
            self.stop_requested = False

    def stop_processing(self):
        self.stop_requested = True
        self.status_var.set("正在停止...")
        self.log_message("正在停止所有线程...")

        # 清空任务队列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except:
                pass

    def extract_dialogues(self):
        """提取对话"""
        if not self.rpy_folder_path.get():
            messagebox.showerror("错误", "请选择RPY文件夹")
            return

        if not self.character_file_path.get():
            messagebox.showerror("错误", "请选择角色定义文件")
            return

        if not self.extract_output_path.get():
            messagebox.showerror("错误", "请选择输出目录")
            return

        # 检查路径是否存在
        if not os.path.exists(self.rpy_folder_path.get()):
            messagebox.showerror("错误", "RPY文件夹不存在")
            return

        if not os.path.exists(self.character_file_path.get()):
            messagebox.showerror("错误", "角色定义文件不存在")
            return

        # 创建输出目录（如果不存在）
        os.makedirs(self.extract_output_path.get(), exist_ok=True)

        # 禁用按钮，防止重复点击
        self.extract_button.config(state=tk.DISABLED)
        self.extract_result_text.delete(1.0, tk.END)
        self.extract_result_text.insert(tk.END, "正在提取对话，请稍候...\n")

        # 在新线程中执行提取操作
        thread = threading.Thread(target=self.do_extract_dialogues)
        thread.daemon = True
        thread.start()

    def do_extract_dialogues(self):
        """执行对话提取"""
        try:
            result = self.dialogue_extractor.process_rpy_files(
                self.rpy_folder_path.get(),
                self.character_file_path.get(),
                self.extract_output_path.get()
            )

            # 更新结果文本框
            self.extract_result_text.delete(1.0, tk.END)
            self.extract_result_text.insert(tk.END, "提取完成!\n\n")
            self.extract_result_text.insert(tk.END, f"对话条数: {result['dialogues_count']}\n")
            self.extract_result_text.insert(tk.END, f"旁白条数: {result['narrations_count']}\n")
            self.extract_result_text.insert(tk.END, f"角色数量: {result['characters_count']}\n\n")
            self.extract_result_text.insert(tk.END, f"旁白文件: {result['narration_file']}\n")

            for file_path in result['character_files']:
                self.extract_result_text.insert(tk.END, f"角色文件: {file_path}\n")

        except Exception as e:
            self.extract_result_text.delete(1.0, tk.END)
            self.extract_result_text.insert(tk.END, f"提取过程中出错: {str(e)}")
        finally:
            # 重新启用按钮
            self.extract_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = TTSGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()