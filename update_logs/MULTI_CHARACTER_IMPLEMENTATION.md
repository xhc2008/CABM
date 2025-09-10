# 多角色对话功能实现文档

## 概述

本次实现为剧情模式添加了多角色对话支持（尚未完全完成），主要包含以下三个方面的改动：

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

## 9. 后续完善（2025-09-10）

### 9.1 修复导演模型JSON解析问题
- **问题**：导演模型返回的JSON可能被```json```包裹，导致解析失败
- **解决方案**：在`services/story_service.py`中增强JSON解析逻辑
  - 自动检测并移除```json```和```标记
  - 支持混合文本中的JSON提取
  - 增加错误处理和日志记录

### 9.2 实现多角色对话流程
- **角色专用提示词格式**：在`services/chat_service.py`中新增`format_messages_for_character`方法
  - 每个角色只看到自己说的话作为`assistant`消息（包含完整JSON）
  - 其他角色的话提取`content`字段并作为`user`消息的一部分
  - 玩家消息统一标记为"玩家："
  - 角色消息标记为"角色名："

### 9.3 角色自动回复机制
- **工作流程**：在`routes/story_routes.py`中实现完整的角色自动回复
  - 当导演模型指定非玩家角色说话时，自动触发该角色回复
  - 切换到指定角色并构建专用消息格式
  - 调用角色专用的对话API
  - 保存角色回复到历史记录和记忆数据库
  - 再次调用导演模型判断下一个说话者

### 9.4 前端多角色支持
- **流式响应处理**：在`static/js/chat-service.js`中增加多角色事件处理
  - `nextSpeaker`: 下一个说话者信息
  - `characterResponse`: 角色回复开始
  - `characterContent`: 角色回复内容
  - `characterResponseComplete`: 角色回复完成

- **视觉效果服务**：新增`static/js/multi-character-service.js`
  - 角色立绘切换和定位（左侧、右侧、中央）
  - 角色说话时的视觉指示（发光效果）
  - 智能角色布局（单角色居中，多角色分布两侧）

### 9.5 历史记录格式优化
- **多角色模式**：在`utils/history_utils.py`中完善历史记录保存
  - `assistant`消息的`role`字段改为对应的角色ID
  - 支持`speaker_character_id`参数指定说话角色
  - 保持单角色模式的向后兼容性

### 9.6 记忆存储完善
- **故事记忆**：`services/memory_service.py`中的`add_story_message`方法
  - 支持按角色名分别存储消息
  - 每条记忆记录格式："角色名：消息内容"
  - 玩家消息统一使用"玩家"作为角色名

### 9.7 测试验证
创建了`test_multi_character_implementation.py`测试脚本，验证：
- ✅ JSON解析（包括```json```包裹情况）
- ✅ 导演模型调用和角色选择
- ✅ 角色专用消息格式构建
- ✅ 多角色故事记忆存储和检索

## 10. 使用说明

### 10.1 创建多角色故事
```python
# 在故事创建时传入多个角色ID
story_service.create_story(
    story_id="multi_adventure",
    title="多角色冒险",
    character_ids=["Elysia", "Collei"],  # 多个角色
    story_direction="一起探索神秘森林的冒险故事"
)
```

### 10.2 对话流程
1. **玩家输入**：正常发送消息
2. **导演判断**：自动调用导演模型判断下次说话角色
3. **角色回复**：如果是角色说话，自动触发角色回复
4. **视觉切换**：前端自动切换角色立绘和视觉效果
5. **循环继续**：重复上述流程直到故事结束

### 10.3 角色序号分配
- 序号0：玩家
- 序号1：第一个角色（如Elysia）
- 序号2：第二个角色（如Collei）
- 以此类推...

## 11. 技术特性

### 11.1 智能角色切换
- 导演模型基于对话内容和剧情进度智能选择下次说话角色
- 支持角色间的自然对话流转
- 玩家可以随时参与对话

### 11.2 个性化提示词
- 每个角色拥有独立的对话历史视角
- 角色只能看到自己的完整回复（包含mood等信息）
- 其他角色的话只显示content内容

### 11.3 视觉体验
- 动态角色立绘切换
- 说话角色的视觉高亮
- 智能布局适应不同角色数量

### 11.4 记忆系统
- 按角色分别存储对话记忆
- 支持跨角色的记忆检索
- 保持故事连贯性

---

**实现状态**: ✅ 完成
**测试状态**: ✅ 通过（4/4个测试用例）
**兼容性**: ✅ 向后兼容
**新增功能**: ✅ 多角色对话、角色自动回复、视觉切换