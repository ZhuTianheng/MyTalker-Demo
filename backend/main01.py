# import os
# import uuid
# import uvicorn
# import edge_tts
# from fastapi import FastAPI
# from fastapi.staticfiles import StaticFiles
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from openai import OpenAI # 用于调用各类大模型 API

# app = FastAPI()

# # --- 配置区 ---
# # 1. 跨域配置 (保持不变)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 2. 静态文件挂载 (保持不变)
# os.makedirs("static", exist_ok=True)
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # 3. LLM 配置 (DeepSeek)
# # !!! 重要：这里改为 False 才能真的去调用 API !!!
# USE_MOCK_LLM = False 

# # 请在这里填入你的 DeepSeek API Key (以 sk- 开头)
# API_KEY = "sk-fb79e2d9430144d583a031002858fbf8" 
# BASE_URL = "https://api.deepseek.com" 

# # --- 核心功能函数 ---

# # 功能 1: LLM 文本生成 (DeepSeek 版本)
# def get_llm_response(user_text):
#     # 如果你没有 Key，或者想省钱调试，可以把上面改回 True
#     if USE_MOCK_LLM:
#         return f"【测试模式】我收到了：{user_text}。DeepSeek 接口未开启，这是本地模拟回复。"
    
#     try:
#         # 初始化 OpenAI 客户端，但指向 DeepSeek 的服务器
#         client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        
#         response = client.chat.completions.create(
#             model="deepseek-chat",  # DeepSeek 的模型名称
#             messages=[
#                 # system prompt: 设定数字人的性格
#                 {"role": "system", "content": "你是一个幽默、亲切的数字人助手。请用简短的口语回答用户，不要使用Markdown格式，字数控制在10字以内。"},
#                 {"role": "user", "content": user_text},
#             ],
#             stream=False # 简单起见，先不使用流式输出
#         )
        
#         # 提取回复内容
#         return response.choices[0].message.content
        
#     except Exception as e:
#         print(f"DeepSeek 调用失败: {e}")
#         return "抱歉，我的大脑（LLM接口）刚刚断线了，请检查 API Key 或网络。"

# # 功能 2: TTS 语音合成 (异步)
# async def generate_audio(text, output_filename):
#     # voice 列表: zh-CN-XiaoxiaoNeural (女), zh-CN-YunxiNeural (男)
#     voice = "zh-CN-YunyangNeural"
#     communicate = edge_tts.Communicate(text, voice)
#     await communicate.save(output_filename)

# # --- 接口定义 ---

# class ChatRequest(BaseModel):
#     text: str

# @app.post("/api/generate")
# async def generate_video(request: ChatRequest):
#     print(f"1. 收到用户输入: {request.text}")
    
#     # 第一步：LLM 生成文本
#     ai_text = get_llm_response(request.text)
#     print(f"2. LLM 回复: {ai_text}")
    
#     # 第二步：TTS 生成音频
#     # 使用 uuid 生成唯一文件名，防止冲突
#     unique_id = uuid.uuid4().hex
#     audio_filename = f"audio_{unique_id}.mp3"
#     audio_path = os.path.join("static", audio_filename)
    
#     await generate_audio(ai_text, audio_path)
#     print(f"3. 音频已生成: {audio_path}")
    
#     # 第三步：数字人生成视频 (暂时先用假视频占位)
#     # ！！！下一步我们将替换这里 ！！！
#     # 目前我们把生成的音频回传给前端，先验证声音对不对
#     video_url = "/static/demo.mov" # 还是原来的大白兔
    
#     return {
#         "response_text": ai_text,
#         "video_url": video_url,
#         "audio_url": f"/static/{audio_filename}" # 新增：返回音频地址供调试
#     }

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)


import os
import uuid
import time
import shutil
import subprocess
import uvicorn
import edge_tts
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from datetime import datetime

app = FastAPI()

# --- 配置区 ---
# 1. 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 静态文件挂载
# myEgst 项目内的静态目录，用于前端访问
LOCAL_STATIC_DIR = "static"
os.makedirs(LOCAL_STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=LOCAL_STATIC_DIR), name="static")

# 3. LLM 配置 (使用你之前的配置)
USE_MOCK_LLM = False
API_KEY = "sk-fb79e2d9430144d583a031002858fbf8"  # 记得填回你的 Key
BASE_URL = "https://api.deepseek.com"

# --- 数字人引擎配置 (源自 show_egst.py) ---
class DigitalHumanEngine:
    def __init__(self):
        # 基础路径
        self.BASE_DIR = "/home/zth/EGSTalker2"
        self.KAN_PATH = os.path.join(self.BASE_DIR, "scene/KAN")
        
        # 模型输出的固定路径
        self.MODEL_OUTPUT_FILE = os.path.join(
            self.BASE_DIR, 
            "output_gsat/kan-pee-a200-b16/custom/ours_10000/renders/output_gsat_custom_10000iter_renders.mov"
        )
        self.TEMP_CUSTOM_DIR = os.path.join(self.BASE_DIR, "output_gsat/kan-pee-a200-b16/custom")

    def _get_env(self):
        """构造包含 KAN 路径的环境变量"""
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{current_pythonpath}:{self.KAN_PATH}"
        return env

    def run_cmd(self, cmd_list, description):
        """执行 Shell 命令"""
        print(f"Executing: {' '.join(cmd_list)}")
        result = subprocess.run(
            cmd_list,
            cwd=self.BASE_DIR, # 关键：必须在 EGSTalker2 根目录下运行
            env=self._get_env(), # 注入环境变量
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ {description} 失败:\nStderr: {result.stderr}\nStdout: {result.stdout}")
            raise Exception(f"{description} Failed")
        return True

    def process(self, audio_mp3_path, output_video_filename):
        """执行完整的数字人生成流程"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 1. 准备临时文件路径 (WAV 用于模型输入)
        # 我们暂时把生成的中间文件放在 static 里，方便管理
        wav_path = audio_mp3_path.replace(".mp3", ".wav")
        npy_path = audio_mp3_path.replace(".mp3", ".npy")

        # 2. MP3 转 WAV (16k采样率，模型通用要求) 
        # 使用 ffmpeg 替代原来的 changeWav.py，更稳健
        cmd_ffmpeg = [
            "ffmpeg", "-y", "-i", audio_mp3_path, 
            "-ar", "16000", "-ac", "1", wav_path
        ]
        self.run_cmd(cmd_ffmpeg, "音频格式转换")

        # 3. 提取音频特征 (extract_ds_features.py) 
        cmd_extract = [
            "python", "data_utils/deepspeech_features/extract_ds_features.py",
            "--input", wav_path
        ]
        self.run_cmd(cmd_extract, "音频特征提取")

        # 4. 数字人渲染 (render.py) 
        # 注意：这里我们使用绝对路径，确保不依赖相对路径的歧义
        cmd_render = [
            "python", "render.py",
            "-s", "datasets/Obama", # 相对 BASE_DIR 的路径
            "--model_path", "output_gsat/kan-pee-a200-b16",
            "--configs", "arguments/64_dim_1_transformer.py",
            "--iteration", "10000",
            "--batch", "1", # 你的代码里是 16，但单次推理建议用 1 加快速度，或者保持 16
            "--custom_aud", npy_path, # 传入刚才生成的特征文件
            "--custom_wav", wav_path,
            "--skip_train",
            "--skip_test"
        ]
        self.run_cmd(cmd_render, "数字人视频渲染")

        # 5. 移动结果文件 
        if os.path.exists(self.MODEL_OUTPUT_FILE):
            final_video_path = os.path.join(LOCAL_STATIC_DIR, output_video_filename)
            shutil.copy(self.MODEL_OUTPUT_FILE, final_video_path)
            print(f"Video saved to: {final_video_path}")
            
            # 6. 清理临时目录 (custom文件夹) 
            if os.path.exists(self.TEMP_CUSTOM_DIR):
                shutil.rmtree(self.TEMP_CUSTOM_DIR)
                
            return f"/static/{output_video_filename}"
        else:
            raise Exception("Render script finished but output video not found.")

# 初始化引擎
engine = DigitalHumanEngine()

# --- 核心功能函数 ---

def get_llm_response(user_text):
    if USE_MOCK_LLM:
        return f"【测试】收到：{user_text}。正在驱动数字人生成视频，请稍候..."
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个数字人助手，请用口语化简短回答(20字以内)。"},
                {"role": "user", "content": user_text},
            ],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "网络开小差了，但我还在。"

async def generate_audio_file(text):
    """生成 TTS 音频并保存"""
    unique_id = uuid.uuid4().hex
    filename = f"audio_{unique_id}.mp3"
    filepath = os.path.join(LOCAL_STATIC_DIR, filename)
    
    # 这里的绝对路径是必须的，方便后面ffmpeg调用
    abs_filepath = os.path.abspath(filepath)
    
    communicate = edge_tts.Communicate(text, "zh-CN-YunyangNeural")
    await communicate.save(abs_filepath)
    return abs_filepath, filename

# --- 接口定义 ---

class ChatRequest(BaseModel):
    text: str

@app.post("/api/generate")
async def generate_video_endpoint(request: ChatRequest):
    print(f"1. 收到请求: {request.text}")
    
    try:
        # Step 1: LLM
        ai_text = get_llm_response(request.text)
        print(f"2. LLM回复: {ai_text}")
        
        # Step 2: TTS
        audio_abs_path, audio_filename = await generate_audio_file(ai_text)
        print(f"3. 音频生成: {audio_abs_path}")
        
        # Step 3: Digital Human Render
        # 视频文件名
        video_filename = audio_filename.replace(".mp3", ".mp4")
        
        print("4. 开始渲染数字人 (耗时操作)...")
        video_url = engine.process(audio_abs_path, video_filename)
        print(f"5. 渲染完成: {video_url}")
        
        return {
            "response_text": ai_text,
            "video_url": video_url
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "response_text": "抱歉，生成视频时出错了。",
            # 出错时返回一个默认视频，防止前端崩坏
            "video_url": "/static/demo.mp4" 
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)