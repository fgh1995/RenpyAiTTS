import re

# 读取name.rpy文件内容
with open('C:/Users/Administrator/Downloads/bbn-vn-demo-pc/BoundbyNight-0.17a-pc/game/tl/schinese/base/name.rpy', 'r',
          encoding='utf-8') as f:
    name_content = f.read()

# 提取翻译映射
translation_pattern = r'old "([^"]+)"\s+new "([^"]+)"'
translations = dict(re.findall(translation_pattern, name_content))

# 读取包含角色定义的.rpy文件
with open('C:/Users/Administrator/Downloads/bbn-vn-demo-pc/BoundbyNight-0.17a-pc/game/script.rpy', 'r',
          encoding='utf-8') as f:
    char_content = f.read()

# 改进的正则表达式，匹配所有Character定义格式
char_pattern = r'define\s+(\w+)\s*=\s*Character\("([^"]+)"(?:,[^)]+)?\)'
characters = re.findall(char_pattern, char_content)

print(f"找到 {len(characters)} 个角色定义:")
for var_name, eng_name in characters:
    print(f"{var_name} = {eng_name}")

# 创建角色到中文名的映射
char_translation = {}
for var_name, eng_name in characters:
    # 精确匹配大小写
    if eng_name in translations:
        char_translation[var_name] = translations[eng_name]
    else:
        char_translation[var_name] = eng_name  # 如果没有翻译，保持英文原文

# 生成新的.rpy文件内容 - 使用 x = x 格式
output_content = "# 角色定义 - 中文版\n\n"
for var_name, eng_name in characters:
    chinese_name = char_translation[var_name]

    # 直接创建新的定义行，使用 x = x 格式
    if chinese_name == eng_name:
        # 如果没有翻译，保持原格式
        new_line = f'{var_name} = {eng_name}'
    else:
        # 如果有翻译，使用中文名
        new_line = f'{var_name} = {chinese_name}'

    output_content += new_line + '\n'

# 写入输出文件
with open('C:/Users/Administrator/Downloads/bbn-vn-demo-pc/BoundbyNight-0.17a-pc/角色定义中文版.txt', 'w',
          encoding='utf-8') as f:
    f.write(output_content)

print(f"\n处理完成！共处理了 {len(characters)} 个角色定义")
print("角色定义已成功转换为中文并保存到 角色定义中文版.txt")

# 打印处理结果以便检查
print("\n处理结果：")
translated_count = 0
for var_name, eng_name in characters:
    chinese_name = char_translation[var_name]
    status = "✓ 已翻译" if chinese_name != eng_name else "✗ 保持原文"
    print(f"{var_name} = {eng_name} -> {chinese_name} ({status})")
    if chinese_name != eng_name:
        translated_count += 1

print(f"\n翻译统计：{translated_count} 个已翻译，{len(characters) - translated_count} 个保持原文")