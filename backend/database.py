from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# 1. 数据库地址 (当前目录下生成 chat_history.db)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@127.0.0.1:3306/digital_human_db"

# 2. 创建引擎
# check_same_thread=False 是 SQLite 必须的配置，因为 FastAPI 是多线程的
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# 3. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 基础类
Base = declarative_base()

# --- 定义表模型 ---
class ChatRecord(Base):
    __tablename__ = "chat_records"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now) # 时间
    role = Column(String(20))          # user (用户) / ai (数字人)
    content_type = Column(String(20))  # text / video / error
    content = Column(Text)             # 文字内容 或 视频URL
    status = Column(String(20))        # success / pending / failed
    process_time = Column(Integer, nullable=True) # 耗时(秒)

# 5. 自动建表 (如果表不存在，会自动创建)
Base.metadata.create_all(bind=engine)

# 6. 获取数据库会话的依赖函数 (给 FastAPI 用)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()