import os
import re


def extract_text_from_rpy(file_path):
    """
    从.rpy文件中提取角色对话（包含角色代码）和旁白文本

    Args:
        file_path (str): .rpy文件的路径

    Returns:
        dict: 包含提取的对话（带角色代码）和旁白的字典
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

    dialogues = []  # 格式: (角色代码, 文本)
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
                        dialogues.append((character_code, cleaned_text.strip()))
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


def process_rpy_files(folder_path):
    """
    处理文件夹中的所有.rpy文件

    Args:
        folder_path (str): 文件夹路径
    """
    all_dialogues = []  # 格式: (角色代码, 文本)
    all_narrations = []  # 格式: 文本

    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.rpy'):
                file_path = os.path.join(root, file)
                print(f"处理文件: {file_path}")

                # 提取文本
                result = extract_text_from_rpy(file_path)
                all_dialogues.extend(result["dialogues"])
                all_narrations.extend(result["narrations"])

    # 输出结果
    print("\n=== 角色对话（带角色代码） ===")
    for i, (character, dialogue) in enumerate(all_dialogues, 1):
        print(f"{i}. [{character}] {dialogue}")

    print("\n=== 旁白 ===")
    for i, narration in enumerate(all_narrations, 1):
        print(f"{i}. {narration}")

    # 保存到文件
    output_file = os.path.join(folder_path, 'extracted_text.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== 角色对话（带角色代码） ===\n")
        for i, (character, dialogue) in enumerate(all_dialogues, 1):
            f.write(f"{i}. [{character}] {dialogue}\n")

        f.write("\n=== 旁白 ===\n")
        for i, narration in enumerate(all_narrations, 1):
            f.write(f"{i}. {narration}\n")

    # 分别保存角色对话和旁白到不同的文件
    dialogue_file = os.path.join(folder_path, 'dialogues_only.txt')
    with open(dialogue_file, 'w', encoding='utf-8') as f:
        for character, dialogue in all_dialogues:
            f.write(f"{dialogue}\n")

    narration_file = os.path.join(folder_path, 'narrations_only.txt')
    with open(narration_file, 'w', encoding='utf-8') as f:
        for narration in all_narrations:
            f.write(f"{narration}\n")

    # 按角色分类统计
    character_stats = {}
    for character, dialogue in all_dialogues:
        if character not in character_stats:
            character_stats[character] = []
        character_stats[character].append(dialogue)

    # 保存按角色分类的对话
    for character, lines in character_stats.items():
        char_file = os.path.join(folder_path, f'dialogue_{character}.txt')
        with open(char_file, 'w', encoding='utf-8') as f:
            for i, dialogue in enumerate(lines, 1):
                f.write(f"{i}. {dialogue}\n")

    print(f"\n统计结果:")
    print(f"总对话条数: {len(all_dialogues)}")
    print(f"总旁白条数: {len(all_narrations)}")
    print(f"角色数量: {len(character_stats)}")
    print(f"\n角色对话统计:")
    for character, lines in character_stats.items():
        print(f"  {character}: {len(lines)} 条")

    print(f"\n结果已保存到:")
    print(f"  - 完整提取: {output_file}")
    print(f"  - 纯对话文本: {dialogue_file}")
    print(f"  - 纯旁白文本: {narration_file}")
    for character in character_stats.keys():
        print(f"  - {character} 的对话: dialogue_{character}.txt")


# 使用示例
if __name__ == "__main__":
    folder_path = r"C:\360极速浏览器X下载\仅机翻补丁-[CHS]BoundbyNight-0.17a-pc\game\tl\schinese\voice"

    if os.path.exists(folder_path):
        process_rpy_files(folder_path)
    else:
        print(f"文件夹路径不存在: {folder_path}")
        print("请确保路径正确，或者使用绝对路径")