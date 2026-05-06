<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import axios from 'axios'

// --- 状态变量 ---
const inputText = ref('')
const loading = ref(false)
const currentVideoSrc = ref('') // 当前正在播放的视频
const rawHistory = ref([])      // 从后端获取的原始记录

// --- 配置 ---
const API_BASE_URL = 'http://localhost:8000'

// --- 计算属性：处理对话列表 ---
// 我们把后端返回的记录处理一下，方便渲染气泡
// 并且把顺序反转，让最新的消息在最下面（符合聊天习惯）
// 修改 script 中的 chatList 计算属性
const chatList = computed(() => {
  return rawHistory.value.slice().reverse().map(item => {
    let displayContent = item.content
    let videoUrl = ''
    
    // 如果是 AI 且成功状态，尝试拆分内容
    if (item.role === 'ai' && item.status === 'success' && item.content.includes('|||')) {
      const parts = item.content.split('|||')
      displayContent = parts[0] // 前半部分是文字
      videoUrl = parts[1]       // 后半部分是链接
    } else if (item.role === 'ai' && item.content_type === 'video') {
       // 兼容旧数据（只有链接的情况）
       videoUrl = item.content
       displayContent = "（点击播放视频）"
    }

    return {
      id: item.id,
      role: item.role,
      type: item.content_type,
      content: displayContent, // 这里现在只显示文字
      videoUrl: videoUrl,      // 单独存视频链接
      isVideo: !!videoUrl      // 标记是否包含视频
    }
  })
})

// --- 方法 ---

// 1. 获取历史记录
const fetchHistory = async () => {
  try {
    // 获取最近 50 条
    const res = await axios.get(`${API_BASE_URL}/api/history`)
    rawHistory.value = res.data
    scrollToBottom()
  } catch (error) {
    console.error("获取历史失败", error)
  }
}

// 2. 发送消息
const handleSend = async () => {
  if (!inputText.value.trim()) return

  const textToSend = inputText.value
  inputText.value = '' // 清空输入框
  loading.value = true

  // 乐观更新：先把用户的话显示在界面上（不等后端）
  // 注意：这里只是临时显示，真正的数据还是等 fetchHistory 刷新
  rawHistory.value.unshift({
    id: Date.now(),
    role: 'user',
    content_type: 'text',
    content: textToSend,
    created_at: new Date().toISOString()
  })
  scrollToBottom()

  try {
    const res = await axios.post(`${API_BASE_URL}/api/generate`, {
      text: textToSend
    })

    // 后端返回了：response_text (AI的文字) 和 video_url (AI的视频)
    // 1. 自动播放视频
    currentVideoSrc.value = `${API_BASE_URL}${res.data.video_url}`
    
    // 2. 刷新历史记录 (这样 AI 的回复就会出现在列表中)
    await fetchHistory()
    
  } catch (error) {
    console.error(error)
    alert("生成失败，请检查后端")
  } finally {
    loading.value = false
  }
}

// 3. 点击历史记录里的视频气泡，在右侧播放
const playHistoryVideo = (url) => {
  currentVideoSrc.value = `${API_BASE_URL}${url}`
}

// 4. 滚动到底部
const chatWindowRef = ref(null)
const scrollToBottom = () => {
  nextTick(() => {
    if (chatWindowRef.value) {
      chatWindowRef.value.scrollTop = chatWindowRef.value.scrollHeight
    }
  })
}

// 初始化
onMounted(() => {
  fetchHistory()
})
</script>

<template>
  <div class="main-layout">
    
    <div class="left-panel">
      
      <div class="chat-header">
        <h3>基于说话人脸视频生成的数字人智能交互系统</h3>
      </div>

      <div class="chat-window" ref="chatWindowRef">
        
        <div v-if="chatList.length === 0" class="empty-tip">
          还没有对话，快去打个招呼吧！
        </div>

        <div 
          v-for="msg in chatList" 
          :key="msg.id" 
          :class="['message-row', msg.role === 'user' ? 'row-user' : 'row-ai']"
        >
          <div class="avatar">
            {{ msg.role === 'user' ? '我' : 'AI' }}
          </div>
          
          <div class="bubble">
            <div class="text-content">
              {{ msg.content }}
            </div>
            
            <div v-if="msg.isVideo" class="video-attachment" @click="playHistoryVideo(msg.videoUrl)">
              <span class="play-icon">▶️</span> 点击播放数字人视频
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <input 
            v-model="inputText" 
            type="text" 
            placeholder="输入您的问题..."
            @keyup.enter="handleSend"
            :disabled="loading"
          />
          <div class="btn-group">
            <button class="btn-send" @click="handleSend" :disabled="loading">
              {{ loading ? '生成中...' : '发送' }}
            </button>
            <button class="btn-cancel" @click="inputText = ''">取消</button>
          </div>
        </div>
      </div>
    </div>

    <div class="right-panel">
      <div class="video-container">
        <video 
          v-if="currentVideoSrc" 
          :src="currentVideoSrc" 
          controls 
          autoplay 
          class="digital-human-video"
        ></video>
        <div v-else class="video-placeholder">
          <p>数字人准备就绪</p>
          <p>等待指令...</p>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* 全局布局：左右分栏 */
.main-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background-color: #f5f7fa;
  overflow: hidden; /* 防止整个页面滚动 */
  /* --- 新增这一行 --- */
  zoom: 0.95; /* 这里控制缩放比例，0.8 就是 80%，0.9 就是 90% */
  /* ---------------- */
}

/* --- 左侧面板 --- */
.left-panel {
  flex: 7; /* 占 70% 宽度 */
  display: flex;
  flex-direction: column;
  border-right: 1px solid #e0e0e0;
  background: white;
  position: relative;
}

/* 标题栏样式 */
.chat-header {
  padding: 15px 0;         /* 上下内边距 */
  text-align: center;      /* 文字居中 */
  border-bottom: 1px solid #eee; /* 底部淡分割线 */
  background-color: #fff;  /*以此保证背景纯白 */
  flex-shrink: 0;          /* 防止被挤压 */
}

.chat-header h3 {
  margin: 0;
  font-size: 32px;         /* 字体大小适中 */
  font-weight: 600;
  color: #333;
}

/* 聊天窗口 */
.chat-window {
  flex: 1; /* 占满剩余高度 */
  overflow-y: auto;
  padding: 10px;
  padding-bottom: 100px; /* 给底部输入框留位置 */
}

.empty-tip {
  text-align: center;
  color: #999;
  margin-top: 50px;
}

/* 消息行 */
.message-row {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.row-user {
  flex-direction: row-reverse; /* 用户消息靠右 */
}

.row-ai {
  flex-direction: row; /* AI 消息靠左 */
}

/* 头像 */
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  color: white;
  margin: 0 10px;
  flex-shrink: 0;
}

.row-user .avatar { background-color: #007bff; }
.row-ai .avatar { background-color: #42b883; }

/* 气泡 */
.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  white-space: pre-wrap; /* 保持换行格式 */
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  text-align: left;
}

.row-user .bubble {
  background-color: #e3f2fd;
  color: #333;
  border-top-right-radius: 2px;
}

.row-ai .bubble {
  background-color: #f1f1f1;
  color: #333;
  border-top-left-radius: 2px;
}

/* 视频链接气泡 */
.video-link-content {
  cursor: pointer;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
}
.video-link-content:hover {
  color: #42b883;
}

/* --- 底部输入区 --- */
.input-area {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #eee;
  padding: 10px;
  z-index: 10;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 90%;
  margin: 0 auto;
}

input {
  width: 100%;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  outline: none;
  transition: border 0.3s;
}

input:focus {
  border-color: #42b883;
}

.btn-group {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

button {
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-send {
  background-color: #333;
  color: white;
}
.btn-send:hover { background-color: #000; }
.btn-send:disabled { background-color: #ccc; }

.btn-cancel {
  background-color: #f5f5f5;
  color: #666;
}
.btn-cancel:hover { background-color: #e0e0e0; }

/* --- 右侧面板 --- */
.right-panel {
  flex: 3; /* 占 30% 宽度 */
  background-color: #000;
  display: flex;
  align-items: flex-start; /* 视频靠上 */
  justify-content: center;
  padding-top: 20px;
}

.video-container {
  width: 90%;
  aspect-ratio: 9/16; /* 竖屏比例，如果是横屏可以改 16/9 */
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

.digital-human-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 14px;
}

/* 新增视频附件样式 */
.video-attachment {
  margin-top: 8px;
  padding: 8px;
  background: rgba(0,0,0,0.05);
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #42b883;
  display: flex;
  align-items: center;
  gap: 5px;
}
.video-attachment:hover {
  background: rgba(0,0,0,0.1);
}

</style>