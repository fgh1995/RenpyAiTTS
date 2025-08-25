import os
import re


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
                        print(f"加载角色翻译: {character_code} -> {chinese_name}")

    except Exception as e:
        print(f"读取角色定义文件时出错: {e}")

    return translation_dict


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
        print(f"处理文件 {file_path} 时出错: {e}")
        return {"dialogues": [], "narrations": []}

    return {
        "dialogues": dialogues,
        "narrations": narrations
    }


def process_rpy_files(folder_path, translation_dict):
    """
    处理文件夹中的所有.rpy文件

    Args:
        folder_path (str): 文件夹路径
        translation_dict (dict): 角色代码到中文名称的映射字典
    """
    all_dialogues = []  # 格式: (角色中文名, 文本)
    all_narrations = []  # 格式: 文本

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.rpy'):
                file_path = os.path.join(root, file)
                print(f"处理文件: {file_path}")

                # 提取文本
                result = extract_text_from_rpy(file_path, translation_dict)
                all_dialogues.extend(result["dialogues"])
                all_narrations.extend(result["narrations"])

    print("\n=== 旁白 ===")
    for i, narration in enumerate(all_narrations, 1):
        print(f"None:{narration}")

    # 保存旁白到文件
    narration_file = os.path.join(folder_path, '旁白.txt')
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
        char_file = os.path.join(folder_path, f'dialogue_{safe_filename}.txt')
        with open(char_file, 'w', encoding='utf-8') as f:
            for dialogue in lines:
                f.write(f"{character}:{dialogue}\n")

    print(f"\n统计结果:")
    print(f"总对话条数: {len(all_dialogues)}")
    print(f"总旁白条数: {len(all_narrations)}")
    print(f"角色数量: {len(character_stats)}")
    print(f"\n角色对话统计:")
    for character, lines in character_stats.items():
        print(f"  {character}: {len(lines)} 条")

    print(f"\n结果已保存到:")
    print(f"  - 纯旁白文本: {narration_file}")
    for character in character_stats.keys():
        safe_filename = re.sub(r'[\\/*?:"<>|]', '_', character)
        print(f"  - {character} 的对话: dialogue_{safe_filename}.txt")


# 使用示例
if __name__ == "__main__":
    folder_path = r"C:\Users\Administrator\Downloads\bbn-vn-demo-pc\BoundbyNight-0.17a-pc\game\tl\schinese\scripts"
    translation_file = r"C:\Users\Administrator\Downloads\bbn-vn-demo-pc\BoundbyNight-0.17a-pc\角色定义中文版.txt"

    # 检查文件是否存在
    if not os.path.exists(translation_file):
        print(f"角色定义文件不存在: {translation_file}")
        print("请确保文件路径正确")
        exit()

    if not os.path.exists(folder_path):
        print(f"文件夹路径不存在: {folder_path}")
        print("请确保路径正确，或者使用绝对路径")
        exit()

    # 加载角色翻译
    print("正在加载角色定义...")
    translation_dict = load_character_translations_from_file(translation_file)

    if translation_dict:
        print(f"成功加载 {len(translation_dict)} 个角色定义")
        process_rpy_files(folder_path, translation_dict)
    else:
        print("未能加载角色定义，请检查文件格式")