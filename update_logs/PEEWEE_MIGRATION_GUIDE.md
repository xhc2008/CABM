# Peewee+FAISS记忆存储迁移指南

## 概述

本项目已将记忆存储系统从JSON格式升级到基于**Peewee ORM + FAISS**的混合存储方案，彻底解决了您提到的JSON文件问题。现在使用真正的**SQLite数据库**进行结构化存储，同时保持高效的向量检索能力。

## 为什么选择Peewee+FAISS？

### 解决的问题
- ❌ **不再使用JSON文件存储元数据**（如之前的`Silver_Wolf_metadata.json`）
- ✅ **使用SQLite数据库**进行结构化存储
- ✅ **保留FAISS向量检索**的高性能
- ✅ **真正的数据库管理**，支持复杂查询、索引、事务等

### 技术架构
- **Peewee ORM**: 轻量级Python ORM，管理SQLite数据库
- **FAISS**: 高性能向量相似度搜索
- **SQLite**: 嵌入式数据库，无需额外服务器
- **混合存储**: 结构化数据存数据库，向量数据存FAISS

## 主要改进

### 1. 真正的数据库存储
- **SQLite数据库**: 替代JSON文件，提供ACID事务支持
- **结构化表设计**: 专门的记忆记录表，包含完整的元数据
- **索引优化**: 自动创建索引，提升查询性能
- **数据完整性**: 外键约束和数据验证

### 2. 丰富的查询功能
- **时间范围查询**: 按时间段检索记忆
- **类型过滤**: 区分对话、故事等不同类型记录
- **相似度排序**: 结合向量相似度和数据库查询
- **统计分析**: 记忆数量、最近活动等统计信息

### 3. 数据管理功能
- **自动清理**: 删除过期记录
- **备份恢复**: 数据库级别的备份
- **数据迁移**: 从旧格式平滑迁移
- **性能监控**: 查询性能和存储统计

## 数据库表结构

```sql
CREATE TABLE memory_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    user_message TEXT,
    assistant_message TEXT,
    timestamp DATETIME NOT NULL,
    record_type VARCHAR(50) DEFAULT 'conversation',
    vector_index INTEGER,
    similarity_score REAL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- 索引
CREATE INDEX idx_character_timestamp ON memory_record(character_name, timestamp);
CREATE INDEX idx_character_type ON memory_record(character_name, record_type);
```

## 安装依赖

```bash
pip install faiss-cpu peewee
```

## 迁移步骤

### 1. 自动迁移（推荐）

运行新的Peewee迁移脚本：

```bash
python migrate_to_peewee.py
```

迁移脚本会：
- 自动检测JSON和FAISS格式的旧数据
- 创建SQLite数据库和表结构
- 迁移所有记忆数据到数据库
- 保留FAISS向量索引
- 备份原始数据

### 2. 手动迁移

```python
from migrate_to_peewee import migrate_character_memory, migrate_story_memory

# 迁移特定角色
migrate_character_memory("角色名称")

# 迁移特定故事
migrate_story_memory("故事ID")
```

## 文件结构变化

### 迁移前（JSON/FAISS格式）
```
data/
├── memory/
│   └── Silver_Wolf/
│       ├── Silver_Wolf_memory.json      # 旧JSON文件
│       ├── Silver_Wolf_metadata.json    # 您提到的JSON元数据文件
│       ├── Silver_Wolf_texts.pkl        # FAISS文本数据
│       └── Silver_Wolf_faiss.index      # FAISS索引
└── saves/
    └── story_id/
        └── ...
```

### 迁移后（Peewee+FAISS格式）
```
data/
├── memory/
│   └── Silver_Wolf/
│       ├── backup_before_peewee/        # 备份目录
│       │   ├── Silver_Wolf_metadata.json
│       │   └── Silver_Wolf_texts.pkl
│       ├── Silver_Wolf_memory.db        # 🎉 SQLite数据库文件
│       └── Silver_Wolf_faiss.index      # FAISS向量索引
└── saves/
    └── story_id/
        ├── story_id_memory.db           # 🎉 故事SQLite数据库
        └── story_id_faiss.index         # FAISS向量索引
```

**重要变化**:
- ❌ 不再有`Silver_Wolf_metadata.json`等JSON文件
- ✅ 使用`Silver_Wolf_memory.db` SQLite数据库
- ✅ 保留FAISS索引文件用于向量检索

## 使用方法

### 基本操作（API保持不变）

```python
from services.memory_service import memory_service

# 初始化角色记忆（现在使用数据库）
memory_service.initialize_character_memory("Silver_Wolf")

# 添加对话（自动存储到数据库）
memory_service.add_conversation("你好", "你好！很高兴见到你")

# 搜索记忆（结合数据库查询和向量检索）
result = memory_service.search_memory("问候")
```

### 新增的数据库功能

```python
# 获取详细统计信息
stats = memory_service.get_memory_stats("Silver_Wolf")
print(f"总记录数: {stats['total_records']}")
print(f"对话记录数: {stats['conversation_records']}")
print(f"最新记录时间: {stats['latest_record_time']}")

# 获取最近对话
memory_db = memory_service.get_current_memory_db()
recent_conversations = memory_db.get_recent_conversations(limit=10)

# 清理旧记录
deleted_count = memory_db.delete_old_records(days=30)
print(f"删除了 {deleted_count} 条30天前的记录")
```

## 配置说明

配置保持不变，位于`config.py`中：

```python
RAG_CONFIG = {
    "Multi_Recall": {
        "Cosine_Similarity": {
            "embed_func": "API",
            "embed_kwds": {
                "base_url": "https://api.siliconflow.cn/v1",
                "api_key": os.getenv("MEMORY_API_KEY"),
                "model": "BAAI/bge-m3"
            },
            "vector_dim": 1024
        }
    }
}
```

## 性能优化

### 1. 数据库优化
- **自动索引**: 角色名称、时间戳、记录类型
- **查询优化**: 使用Peewee ORM的查询优化
- **连接池**: SQLite连接复用
- **事务批处理**: 批量操作使用事务

### 2. 向量检索优化
- **FAISS索引**: 高效的L2距离搜索
- **向量归一化**: 确保相似度计算一致性
- **缓存机制**: 嵌入向量缓存

### 3. 混合查询优化
- **先向量后数据库**: 先FAISS检索，再数据库查询详情
- **相似度阈值**: 过滤低质量匹配
- **结果排序**: 综合相似度和时间排序

## 数据库管理

### 查看数据库内容

```python
from utils.peewee_memory_utils import MemoryRecord

# 查询所有记录
records = MemoryRecord.select().where(MemoryRecord.character_name == "Silver_Wolf")

# 按时间排序
recent_records = MemoryRecord.select().where(
    MemoryRecord.character_name == "Silver_Wolf"
).order_by(MemoryRecord.timestamp.desc()).limit(10)

# 统计查询
from peewee import fn
count = MemoryRecord.select(fn.COUNT()).where(
    MemoryRecord.character_name == "Silver_Wolf"
).scalar()
```

### 数据库备份

```bash
# 备份SQLite数据库
cp data/memory/Silver_Wolf/Silver_Wolf_memory.db backup/

# 或使用SQLite命令
sqlite3 data/memory/Silver_Wolf/Silver_Wolf_memory.db ".backup backup.db"
```

## 故障排除

### 1. 迁移问题

```bash
# 检查迁移日志
python migrate_to_peewee.py

# 验证数据库
python -c "
from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB
from config import get_RAG_config
db = PeeweeChatHistoryVectorDB(get_RAG_config(), character_name='Silver_Wolf')
print(db.get_stats())
"
```

### 2. 依赖问题

```bash
# 安装依赖
pip install peewee faiss-cpu

# 验证安装
python -c "import peewee, faiss; print('依赖安装成功')"
```

### 3. 数据库问题

```bash
# 检查数据库文件
ls -la data/memory/Silver_Wolf/Silver_Wolf_memory.db

# 检查数据库内容
sqlite3 data/memory/Silver_Wolf/Silver_Wolf_memory.db "SELECT COUNT(*) FROM memory_record;"
```

## 回滚方案

如果需要回滚：

1. **恢复旧实现**:
```python
# 在 services/memory_service.py 中
from utils.memory_utils import ChatHistoryVectorDB  # 恢复旧导入
```

2. **使用备份数据**:
```bash
# 恢复备份的JSON/FAISS文件
cp data/memory/Silver_Wolf/backup_before_peewee/* data/memory/Silver_Wolf/
```

## 监控和维护

### 1. 性能监控

```python
import time
from services.memory_service import memory_service

# 测试检索性能
start_time = time.time()
result = memory_service.search_memory("测试查询", "Silver_Wolf")
end_time = time.time()
print(f"检索耗时: {end_time - start_time:.3f}秒")
```

### 2. 数据库维护

```python
# 定期清理
memory_db = memory_service.get_current_memory_db()
deleted = memory_db.delete_old_records(days=90)
print(f"清理了 {deleted} 条旧记录")

# 数据库统计
stats = memory_db.get_stats()
print(f"数据库大小: {os.path.getsize(stats['database_path']) / 1024 / 1024:.2f} MB")
```

## 技术优势

### 相比JSON文件
- ✅ **结构化查询**: SQL查询比JSON解析更高效
- ✅ **数据完整性**: ACID事务保证数据一致性
- ✅ **并发安全**: SQLite支持多进程安全访问
- ✅ **索引优化**: 自动索引提升查询性能

### 相比纯FAISS
- ✅ **丰富元数据**: 存储完整的对话信息
- ✅ **时间查询**: 按时间范围检索记忆
- ✅ **类型分类**: 区分不同类型的记录
- ✅ **统计分析**: 丰富的数据统计功能

## 常见问题

**Q: 为什么不再有JSON文件了？**
A: 现在使用SQLite数据库替代JSON文件，提供更好的性能、数据完整性和查询能力。

**Q: 数据库文件会很大吗？**
A: SQLite非常高效，通常比JSON文件更小，且支持压缩和优化。

**Q: 如何查看数据库内容？**
A: 可以使用SQLite工具或Python代码查看，也可以通过memory_service的统计功能。

**Q: 迁移会丢失数据吗？**
A: 不会，迁移脚本会自动备份所有原始数据。

**Q: 性能如何？**
A: 数据库查询 + FAISS向量检索的组合比纯JSON方案快很多，特别是在大量数据时。

## 总结

新的Peewee+FAISS方案彻底解决了您提到的JSON文件问题：

1. **不再使用JSON存储元数据** - 改用SQLite数据库
2. **保持高性能向量检索** - 继续使用FAISS
3. **提供丰富的数据库功能** - 查询、统计、清理等
4. **向后兼容** - API保持不变，平滑升级

现在您的记忆数据真正存储在数据库中，而不是JSON文件！
