init 999 python:
    import hashlib
    import os
    import requests
    original_say = renpy.say

    def custom_say(who, what, **kwargs):
        # 兼容旧版本的游戏根目录获取方法
        if hasattr(renpy.config, 'basedir'):
            game_root = renpy.config.basedir
        else:
            main_script = renpy.parser.main_script
            game_root = os.path.dirname(os.path.abspath(main_script))
        current_script_dir = os.path.join(game_root, "game")

        # 构建output-voice文件夹路径（与当前.rpy文件同层级）
        voice_dir = os.path.join(current_script_dir, "output-voice")
        # 拼接日志文件路径
        log_file_path = os.path.join(game_root, "dialogue_log.txt")
        try:
            # 生成日志内容
            log_content = str(who)+":"+str(what)
            # 写入日志
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(log_content)

            # 将日志内容转换为SHA1小写编码
            sha1_hash = hashlib.sha1()
            sha1_hash.update(log_content.encode('utf-8'))
            audio_filename = sha1_hash.hexdigest() + ".wav"
            # 构建音频文件路径（当前目录）
            audio_path = os.path.join(voice_dir, audio_filename)
            audio_path = audio_path.replace("\\", "/")
            # 检查文件是否存在，如果存在则播放
            if os.path.exists(audio_path):
                # 使用Ren'Py的高频播放函数
                renpy.sound.play(audio_path)

        except Exception as e:
            renpy.log("Error:"+str(e))

        return original_say(who, what, **kwargs)
    renpy.say = custom_say