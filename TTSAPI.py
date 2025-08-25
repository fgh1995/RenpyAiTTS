import argparse
import sys
import os


class TTSGenerator:
    def __init__(self):
        self.headers = {'Content-Type': 'application/json'}

    def generate_tts(self, text, output_path, model_name="原神-中文-莱欧斯利_ZH", speed_factor=1.0):
        """生成单个文本的TTS（保持原有代码不变）"""
        # 这里保持您原有的requests代码不变
        import requests
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
    parser = argparse.ArgumentParser(description='TTS生成工具')
    parser.add_argument('--text', required=True, help='要合成的文本')
    parser.add_argument('--output', required=True, help='输出文件路径')
    parser.add_argument('--model', default='原神-中文-莱欧斯利_ZH', help='模型名称')
    parser.add_argument('--speed', type=float, default=1.0, help='语速因子')

    args = parser.parse_args()

    tts = TTSGenerator()
    success = tts.generate_tts(
        text=args.text,
        output_path=args.output,
        model_name=args.model,
        speed_factor=args.speed
    )

    if success:
        print(f"TTS生成成功，文件保存至: {args.output}")
        sys.exit(0)
    else:
        print("TTS生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()