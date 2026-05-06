import asyncio
import edge_tts

async def test():
    text = "你好，这是一个测试音频。"
    communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
    try:
        await communicate.save("test_audio.mp3")
        print("✅ TTS 生成成功，保存为 test_audio.mp3")
    except Exception as e:
        print(f"❌ TTS 生成失败: {e}")

if __name__ == "__main__":
    asyncio.run(test())
    