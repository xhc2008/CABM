# 多角色对话功能实现文档

## 概述

本次实现为剧情模式添加了多角色对话支持，主要包含以下三个方面的改动：

## 1. 导演模型改进

### 改动内容
- **提示词修改**：导演模型现在返回JSON格式，包含`offset`和`next`两个字段
- **角色列表**：在提示词中列出所有角色（包括玩家）
- **返回格式**：
  ```json
  {
    "offset": 1,  // 0-9的偏移值
    "next": 2     // 下次说话的角色序号
  }
  ```

### 相关文件
- `config.py`: 修改了`DIRECTOR_SYSTEM_PROMPTS`和`get_director_prompts`函数
- `services/story_service.py`: 修改了`call_director_model`方法，新增了`get_story_characters`方法

### 逻辑处理
- 如果`next`指向玩家（序号0），则正常等待用户输入
- 如果`next`指向角色，则可以实现角色自动回复（预留接口）
- 解析失败时随机选择角色

## 2. 历史记录格式改进

### 改动内容
- **单角色模式**：保持原有格式（`user`/`assistant`）
- **多角色模式**：
  - `user`消息保持不变
  - `assistant`消息的`role`字段改为对应的角色ID

### 示例对比
```json
// 单角色模式
{"role": "user", "content": "你好"}
{"role": "assistant", "content": "{\"content\": \"你好！\", \"mood\": 1}"}

// 多角色模式  
{"role": "user", "content": "你好"}
{"role": "Elysia", "content": "{\"content\": \"你好！\", \"mood\": 1}"}
{"role": "Collei", "content": "{\"content\": \"我也向你问好\", \"mood\": 2}"}
```

### 相关文件
- `utils/history_utils.py`: 修改了`save_message`和`save_message_to_file`方法
- `services/chat_service.py`: 修改了消息保存逻辑
- `routes/story_routes.py`: 更新了历史记录保存调用

## 3. 记忆存储格式改进

### 改动内容
- **旧格式**：每条记忆是一轮对话（"用户：...助手：..."）
- **新格式**：每条记忆是一个角色的一次话
  - 玩家的角色名固定为"玩家"
  - 角色使用配置中的`name`字段
  - 只记录`content`字段，不存储完整JSON

### 示例对比
```
// 旧格式
"用户：你好\nElysia：你好！很高兴见到你"

// 新格式
"玩家：你好"
"爱莉希雅：你好！很高兴见到你"
```

### 相关文件
- `utils/memory_utils.py`: 修改了`add_chat_turn`方法，新增了`add_single_message`方法
- `services/memory_service.py`: 新增了`add_story_message`方法
- `routes/story_routes.py`: 更新了记忆存储逻辑

## 4. 兼容性处理

### 向后兼容
- 单角色故事完全兼容原有格式
- 旧的历史记录和记忆数据不受影响
- 新功能仅在多角色故事中启用

### 检测逻辑
```python
# 检查是否为多角色故事
characters = story_data.get('characters', {}).get('list', [])
if isinstance(characters, str):
    characters = [characters]  # 兼容旧格式
is_multi_character = len(characters) > 1
```

## 5. 测试验证

创建了`test_multi_character.py`测试脚本，验证了：
- ✅ 导演模型JSON格式返回
- ✅ 多角色记忆存储格式
- ✅ 多角色历史记录格式
- ✅ 角色列表获取功能

## 6. 使用方式

### 创建多角色故事
在创建故事时，`character_ids`参数传入多个角色ID的列表：
```python
story_service.create_story(
    story_id="multi_story",
    title="多角色冒险",
    character_ids=["Elysia", "Collei"],  # 多个角色
    story_direction="一起冒险的故事"
)
```

### 角色序号分配
- 序号0：玩家
- 序号1：第一个角色（如Elysia）
- 序号2：第二个角色（如Collei）
- 以此类推...

## 7. 后续扩展

### 角色自动回复
当导演模型指定非玩家角色说话时，可以实现：
- 自动触发该角色的回复
- 跳过用户输入等待
- 实现真正的多角色对话流

### 角色切换
可以根据剧情需要动态切换主要角色，实现更丰富的叙事体验。

## 8. 注意事项

1. **API调用**：导演模型需要支持JSON格式输出
2. **错误处理**：解析失败时会随机选择角色，确保系统稳定性
3. **性能考虑**：多角色记忆存储会增加向量数据库的条目数量
4. **UI适配**：前端需要适配多角色的显示格式

---

**实现状态**: ✅ 完成
**测试状态**: ✅ 通过
**兼容性**: ✅ 向后兼容