init 999 python:
    import hashlib
    import os
    original_say = renpy.say

    def custom_say(who, what, **kwargs):
        # 兼容旧版本的游戏根目录获取方法
        if hasattr(renpy.config, 'basedir'):
            game_root = renpy.config.basedir
        else:
            main_script = renpy.parser.main_script
            game_root = os.path.dirname(os.path.abspath(main_script))
        
        current_script_dir = os.path.join(game_root, "game")
        
        # 构建 output-voice 文件夹路径（与 game 文件夹同级？实际在 game 内部）
        voice_dir = os.path.join(current_script_dir, "output-voice")
        
        # 拼接日志文件路径（游戏根目录下）
        log_file_path = renpy.os.path.join(game_root, "dialogue_log.txt")
        
        try:
            # 生成日志内容
            log_content = str(who) + ": " + str(what)
            
            # 写入日志（追加模式，UTF-8编码）
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_content + "\n")  # 添加换行符，使每条日志独立一行
            
            # 将日志内容转换为 SHA1 小写编码
            sha1_hash = hashlib.sha1()
            sha1_hash.update(log_content.encode('utf-8'))
            audio_filename = sha1_hash.hexdigest() + ".wav"
            
            # 构建音频文件路径
            audio_path = os.path.join(voice_dir, audio_filename)
            audio_path = audio_path.replace("\\", "/")  # 统一为 Unix 风格路径
            
            # 检查文件是否存在，如果存在则播放
            if os.path.exists(audio_path):
                renpy.sound.play(audio_path)  # 修正为 renpy.sound.play
                
        except Exception as e:
            renpy.log("Error: " + str(e))
        
        return original_say(who, what, **kwargs)

    renpy.say = custom_say  # 修正变量名为 renpy.say
