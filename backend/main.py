import os
import time
import shutil
import subprocess
import uvicorn
import edge_tts
import uuid
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy.orm import Session

# 引入刚才写的数据库模块
from database import ChatRecord, get_db

app = FastAPI()

# --- 配置区 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCAL_STATIC_DIR = "static"
os.makedirs(LOCAL_STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=LOCAL_STATIC_DIR), name="static")

# LLM 配置
USE_MOCK_LLM = False
API_KEY = "sk-04ed7d0c466e4bc4afc0d425f91d035b" 
BASE_URL = "https://api.deepseek.com"

# --- 数字人引擎  ---
class DigitalHumanEngine:
    def __init__(self):
        self.BASE_DIR = "/home/zth/EGSTalker2"
        self.KAN_PATH = os.path.join(self.BASE_DIR, "scene/KAN")
        self.MODEL_OUTPUT_FILE = os.path.join(
            self.BASE_DIR, 
            "output_gsat/kan-pee-a200-b16/custom/ours_10000/renders/output_gsat_custom_10000iter_renders.mov"
        )
        self.TEMP_CUSTOM_DIR = os.path.join(self.BASE_DIR, "output_gsat/kan-pee-a200-b16/custom")

    def _get_env(self):
        env = os.environ.copy()
        current_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{current_pythonpath}:{self.KAN_PATH}"
        return env

    def run_cmd(self, cmd_list, description):
        print(f"Executing: {' '.join(cmd_list)}")
        result = subprocess.run(
            cmd_list, cwd=self.BASE_DIR, env=self._get_env(), capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ {description} 失败:\nStderr: {result.stderr}")
            raise Exception(f"{description} Failed: {result.stderr}")
        return True

    def process(self, audio_mp3_path, output_video_filename):
        wav_path = audio_mp3_path.replace(".mp3", ".wav")
        npy_path = audio_mp3_path.replace(".mp3", ".npy")

        cmd_ffmpeg = ["ffmpeg", "-y", "-i", audio_mp3_path, "-ar", "16000", "-ac", "1", wav_path]
        self.run_cmd(cmd_ffmpeg, "音频格式转换")

        cmd_extract = ["python", "data_utils/deepspeech_features/extract_ds_features.py", "--input", wav_path]
        self.run_cmd(cmd_extract, "音频特征提取")

        cmd_render = [
            "python", "render.py", "-s", "datasets/Obama", "--model_path", "output_gsat/kan-pee-a200-b16",
            "--configs", "arguments/64_dim_1_transformer.py", "--iteration", "10000", "--batch", "1",
            "--custom_aud", npy_path, "--custom_wav", wav_path, "--skip_train", "--skip_test"
        ]
        self.run_cmd(cmd_render, "数字人视频渲染")

        if os.path.exists(self.MODEL_OUTPUT_FILE):
            final_video_path = os.path.join(LOCAL_STATIC_DIR, output_video_filename)
            shutil.copy(self.MODEL_OUTPUT_FILE, final_video_path)
            if os.path.exists(self.TEMP_CUSTOM_DIR):
                shutil.rmtree(self.TEMP_CUSTOM_DIR)
            return f"/static/{output_video_filename}"
        else:
            raise Exception("Output video not found.")

engine = DigitalHumanEngine()

# --- 辅助函数 ---
def get_llm_response(user_text):
    if USE_MOCK_LLM: return f"【测试】收到：{user_text}"
    try:
        client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": "你是一个数字人助手，请用口语化简短回答(200字以内)。"}, {"role": "user", "content": user_text}],
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return "网络异常，请检查配置。"

# async def generate_audio_file(text):
#     unique_id = uuid.uuid4().hex
#     filename = f"audio_{unique_id}.mp3"
#     filepath = os.path.join(LOCAL_STATIC_DIR, filename)
#     abs_filepath = os.path.abspath(filepath)
#     communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
#     await communicate.save(abs_filepath)
#     return abs_filepath, filename

# main.py

async def generate_audio_file(text):
    if not text or not text.strip():
        text = "我没听清，请再说一次。"
        
    unique_id = uuid.uuid4().hex
    filename = f"audio_{unique_id}.mp3"
    filepath = os.path.join(LOCAL_STATIC_DIR, filename)
    abs_filepath = os.path.abspath(filepath)
    
    print(f"📣 尝试TTS生成 (Voice: Yunxi, Rate: +0%)...")

        try:
        communicate = edge_tts.Communicate(
            text, 
            "zh-CN-YunxiNeural", 
            rate="+0%", 
            volume="+0%"
        )
        await communicate.save(abs_filepath)
        print("✅ TTS 生成成功！")
    except Exception as e:
        print(f"❌ Yunxi 音色尝试失败: {e}")
        # 如果男声失败，再尝试一下另一个女声 'zh-CN-XiaoyiNeural'
        print("🔄 尝试备用音色 Xiaoyi...")
        try:
            communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural", rate="+0%")
            await communicate.save(abs_filepath)
        except Exception as e2:
            raise Exception(f"所有TTS尝试均失败，请检查服务器IP限制: {e2}")
    # ===========================================

    return abs_filepath, filename

# --- 接口定义 ---
class ChatRequest(BaseModel):
    text: str

# 1. 生成接口 (带数据库记录)
@app.post("/api/generate")
async def generate_video_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    # [DB] 记录用户输入
    user_record = ChatRecord(role="user", content_type="text", content=request.text, status="success")
    db.add(user_record)
    db.commit()

    # [DB] 预记录 AI 状态 (pending)
    ai_record = ChatRecord(role="ai", content_type="video", content="", status="pending")
    db.add(ai_record)
    db.commit()
    db.refresh(ai_record) # 刷新以获取 ID

    try:
        ai_text = get_llm_response(request.text)
        print(f"🔍 [Debug] LLM返回内容: '{ai_text}'")  # <--- 添加这行
        if not ai_text or not ai_text.strip():
            raise Exception("LLM 返回了空内容")
        audio_abs_path, audio_filename = await generate_audio_file(ai_text)
        video_filename = audio_filename.replace(".mp3", ".mp4")
        
        # 核心渲染
        video_url = engine.process(audio_abs_path, video_filename)
        
        # [DB] 更新 AI 状态 (success)
        # 修改点：将文字和视频链接拼接存储，中间用 ||| 分隔
        ai_record.content = f"{ai_text}|||{video_url}" 
        ai_record.status = "success"
        ai_record.process_time = int(time.time() - start_time)
        db.commit()
        
        return {"response_text": ai_text, "video_url": video_url}
        
    except Exception as e:
        # [DB] 更新 AI 状态 (failed)
        print(f"Error: {e}")
        ai_record.status = "failed"
        ai_record.content = str(e)[:500] # 记录错误信息
        db.commit()
        return {"response_text": "生成失败", "video_url": "/static/demo.mp4"}

# 2. 历史记录接口 (新加的)
@app.get("/api/history")
def get_history_endpoint(db: Session = Depends(get_db)):
    records = db.query(ChatRecord).order_by(ChatRecord.id.desc()).limit(50).all()
    return records

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)