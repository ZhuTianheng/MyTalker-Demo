import time
from database import SessionLocal, ChatRecord  # 引入你刚才定义的模块

def create_fake_history():
    # 1. 获取数据库会话
    db = SessionLocal()
    
    print("🚀 开始插入演示数据...")

    try:
        # --- 模拟第一条：用户提问 ---
        user_text = "请介绍一下Transformer"
        print(f" -> 正在插入用户提问: {user_text}")
        
        user_record = ChatRecord(
            role="user",
            content_type="text",
            content=user_text,
            status="success",
            process_time=0
        )
        db.add(user_record)
        
        # 为了让时间戳看起来有点间隔，稍微停顿一下（可选）
        # time.sleep(1) 

        # --- 模拟第二条：数字人回答 ---
        # 注意：这里必须严格遵守 "文字|||视频路径" 的格式，否则前端可能会解析失败
        ai_text = "Transformer是一种2017年提出的革命性神经网络架构，其核心是自注意力机制，它让模型在处理序列数据（如文本）时能直接捕捉全局依赖关系，并通过并行计算大幅提升训练效率；这一设计取代了传统的循环神经网络（RNN），直接催生了如BERT（侧重编码）和GPT（侧重解码）等划时代的大语言模型，并逐步扩展至图像、语音等多模态人工智能领域，成为当前AI发展的核心基础。"
        video_path = "/home/zth/myEgst/backend/static/audio_8309133f20054edf8176e77143337717.mp4" # 确保 static 目录下真有这个文件
        
        full_content = f"{ai_text}|||{video_path}"
        
        print(f" -> 正在插入AI回答: {ai_text}")
        print(f" -> 关联视频路径: {video_path}")

        ai_record = ChatRecord(
            role="ai",
            content_type="video",
            content=full_content,
            status="success",       # 关键：状态设为 success 前端才会显示
            process_time=3          # 假装用了3秒
        )
        db.add(ai_record)

        # 3. 提交到数据库
        db.commit()
        print("\n✅ 数据插入成功！")
        print("💡 现在请做两件事：")
        print("1. 确保 backend/static/ 目录下有一个叫 demo.mp4 的视频文件。")
        print("2. 刷新你的前端页面，就能看到这两条完美记录了。")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_fake_history()