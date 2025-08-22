# Peewee+FAISS记忆存储迁移指南

## 概述

本项目已将记忆存储系统从JSON格式升级到基于Peewee ORM + FAISS的混合存储方案，使用真正的SQLite数据库进行结构化存储，同时保持高效的向量检索能力。

## 主要改进

### 1. 性能提升
- **更快的检索速度**: FAISS提供高效的向量相似度搜索
- **更好的扩展性**: 支持大规模向量数据存储
- **内存优化**: 更高效的内存使用

### 2. 检索质量
- **精确的相似度计算**: 基于向量距离的精确匹配
- **更好的语义理解**: 利用嵌入模型的语义表示
- **可调节的相似度阈值**: 过滤低质量匹配结果

### 3. 数据管理
- **结构化存储**: 分离向量、文本和元数据
- **数据一致性**: 自动验证数据完整性
- **备份支持**: 自动创建数据备份

## 安装依赖

在开始迁移之前，请确保安装了必要的依赖：

```bash
pip install faiss-cpu
```

或者如果你有GPU支持：

```bash
pip install faiss-gpu
```

## 迁移步骤

### 1. 自动迁移（推荐）

运行迁移脚本来自动迁移所有现有数据：

```bash
python migrate_to_faiss.py
```

迁移脚本会：
- 自动发现所有角色和故事的记忆数据
- 备份原始JSON文件
- 将数据转换为FAISS格式
- 验证迁移结果

### 2. 手动迁移

如果需要手动迁移特定角色或故事：

```python
from migrate_to_faiss import migrate_character_memory, migrate_story_memory

# 迁移特定角色
migrate_character_memory("角色名称")

# 迁移特定故事
migrate_story_memory("故事ID")
```

## 文件结构变化

### 迁移前（JSON格式）
```
data/
├── memory/
│   └── 角色名/
│       └── 角色名_memory.json
└── saves/
    └── 故事ID/
        └── 故事ID_memory.json
```

### 迁移后（FAISS格式）
```
data/
├── memory/
│   └── 角色名/
│       ├── 角色名_memory_backup.json  # 备份文件
│       ├── 角色名_faiss.index         # FAISS索引
│       ├── 角色名_texts.pkl           # 文本数据
│       └── 角色名_metadata.json       # 元数据
└── saves/
    └── 故事ID/
        ├── 故事ID_memory_backup.json  # 备份文件
        ├── 故事ID_faiss.index         # FAISS索引
        ├── 故事ID_texts.pkl           # 文本数据
        └── 故事ID_metadata.json       # 元数据
```

## 配置说明

FAISS存储使用与原系统相同的RAG配置，位于`config.py`中：

```python
RAG_CONFIG = {
    "Multi_Recall": {
        "Cosine_Similarity": {
            "embed_func": "API",  # 或 "Model"
            "embed_kwds": {
                "base_url": "https://api.siliconflow.cn/v1",
                "api_key": os.getenv("MEMORY_API_KEY"),
                "model": "BAAI/bge-m3"
            },
            "vector_dim": 1024  # 嵌入维度
        }
    }
}
```

## 使用方法

迁移完成后，记忆系统的使用方法保持不变：

```python
from services.memory_service import memory_service

# 初始化角色记忆
memory_service.initialize_character_memory("角色名")

# 添加对话
memory_service.add_conversation("用户消息", "助手回复")

# 搜索记忆
result = memory_service.search_memory("查询内容")
```

## 性能优化建议

### 1. 嵌入模型选择
- **API模式**: 适合生产环境，稳定可靠
- **本地模型**: 适合离线使用，需要GPU支持

### 2. 向量维度
- 默认1024维适合大多数场景
- 可根据嵌入模型调整

### 3. 相似度阈值
- 默认0.3，可在`config.py`中调整
- 较高阈值：更精确但可能遗漏相关内容
- 较低阈值：更全面但可能包含噪音

## 故障排除

### 1. 迁移失败
```bash
# 检查日志输出
python migrate_to_faiss.py

# 手动迁移单个角色
python -c "from migrate_to_faiss import migrate_character_memory; migrate_character_memory('角色名')"
```

### 2. FAISS导入错误
```bash
# 安装FAISS
pip install faiss-cpu

# 验证安装
python -c "import faiss; print('FAISS安装成功')"
```

### 3. 嵌入API错误
- 检查`MEMORY_API_KEY`环境变量
- 验证API端点可访问性
- 确认模型名称正确

### 4. 内存不足
- 减少批处理大小
- 使用更小的嵌入维度
- 分批迁移数据

## 回滚方案

如果需要回滚到JSON格式：

1. 恢复`services/memory_service.py`中的导入：
```python
from utils.memory_utils import ChatHistoryVectorDB
```

2. 使用备份文件恢复数据：
```bash
# 恢复备份文件
find data/ -name "*_backup.json" -exec bash -c 'mv "$1" "${1/_backup/}"' _ {} \;
```

## 监控和维护

### 1. 数据统计
```python
from services.memory_service import memory_service

# 获取统计信息
stats = memory_service.get_memory_stats("角色名")
print(stats)
```

### 2. 定期备份
建议定期备份FAISS文件：
```bash
# 创建备份脚本
tar -czf memory_backup_$(date +%Y%m%d).tar.gz data/memory/ data/saves/
```

### 3. 性能监控
- 监控检索响应时间
- 检查内存使用情况
- 观察检索质量

## 技术细节

### FAISS索引类型
- 使用`IndexFlatL2`：精确L2距离搜索
- 适合中小规模数据（<100万向量）
- 可根据需要升级到其他索引类型

### 向量归一化
- 自动对嵌入向量进行L2归一化
- 确保相似度计算的一致性
- 避免向量长度对结果的影响

### 数据一致性
- 自动验证向量、文本、元数据数量一致性
- 检测并修复数据不匹配问题
- 提供详细的错误日志

## 常见问题

**Q: 迁移会丢失数据吗？**
A: 不会。迁移脚本会自动创建备份文件，原始数据得到保护。

**Q: 迁移需要多长时间？**
A: 取决于数据量和网络速度（如使用API嵌入）。通常几分钟到几十分钟。

**Q: 可以部分迁移吗？**
A: 可以。可以选择性迁移特定角色或故事。

**Q: FAISS文件很大怎么办？**
A: FAISS文件大小与向量数量和维度相关。可以考虑使用压缩索引或清理旧数据。

**Q: 如何验证迁移成功？**
A: 运行应用程序，测试记忆搜索功能，检查返回结果的质量和相关性。

## 支持

如果遇到问题，请：
1. 检查日志输出
2. 验证配置文件
3. 确认依赖安装
4. 查看错误堆栈信息

更多技术支持，请参考项目文档或提交Issue。
