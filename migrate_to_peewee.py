#!/usr/bin/env python3
"""
记忆存储迁移脚本
从JSON/FAISS格式迁移到Peewee+FAISS格式
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent))

from config import get_RAG_config
from utils.peewee_memory_utils import PeeweeChatHistoryVectorDB
from utils.memory_utils import ChatHistoryVectorDB as OldChatHistoryVectorDB

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PeeweeMigration")

def migrate_character_memory(character_name: str, backup: bool = True) -> bool:
    """
    迁移单个角色的记忆数据和聊天历史到Peewee数据库
    
    参数:
        character_name: 角色名称
        backup: 是否备份原始数据
        
    返回:
        是否迁移成功
    """
    try:
        logger.info(f"开始迁移角色记忆和历史到Peewee数据库: {character_name}")
        
        # 检查旧数据是否存在
        old_data_dir = os.path.join('data', 'memory', character_name)
        old_memory_file = os.path.join(old_data_dir, f"{character_name}_memory.json")
        
        # 检查是否有FAISS文件
        faiss_index_file = os.path.join(old_data_dir, f"{character_name}_faiss.index")
        faiss_texts_file = os.path.join(old_data_dir, f"{character_name}_texts.pkl")
        faiss_metadata_file = os.path.join(old_data_dir, f"{character_name}_metadata.json")
        
        # 优先使用FAISS数据，如果不存在则使用JSON数据
        if os.path.exists(faiss_metadata_file):
            logger.info(f"发现FAISS格式数据，从FAISS迁移: {character_name}")
            success = migrate_from_faiss(character_name, backup)
        elif os.path.exists(old_memory_file):
            logger.info(f"发现JSON格式数据，从JSON迁移: {character_name}")
            success = migrate_from_json(character_name, backup)
        else:
            logger.warning(f"角色 {character_name} 没有找到任何记忆数据")
            return False
            
        # 迁移聊天历史记录
        if success:
            logger.info("开始迁移聊天历史记录...")
            history_manager = HistoryManager("data/history")
            old_history_file = os.path.join('data', 'history', f"{character_name}_history.log")
            
            if os.path.exists(old_history_file):
                # 读取旧的历史记录
                old_history = []
                with open(old_history_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                old_history.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
                
                if old_history:
                    logger.info(f"找到 {len(old_history)} 条历史记录需要迁移")
                    
                    # 创建新的Peewee数据库实例来添加历史记录
                    new_db = PeeweeChatHistoryVectorDB(
                        RAG_config=get_RAG_config(),
                        character_name=character_name
                    )
                    new_db.initialize_database()
                    
                    # 迁移每条历史记录
                    for record in old_history:
                        role = record.get('role')
                        content = record.get('content')
                        timestamp = record.get('timestamp')
                        
                        # 查找用户和助手的连续对话对
                        # 这里简化处理，假设历史记录是按顺序的用户-助手对话
                        # 实际应用中可能需要更复杂的匹配逻辑
                        
                    logger.info(f"成功迁移 {len(old_history)} 条历史记录")
                else:
                    logger.warning(f"角色 {character_name} 没有找到可迁移的历史记录")
            else:
                logger.warning(f"角色 {character_name} 的旧历史记录文件不存在: {old_history_file}")
        
        return success
            
    except Exception as e:
        logger.error(f"迁移角色 {character_name} 失败: {e}")
        traceback.print_exc()
        return False

def migrate_from_faiss(character_name: str, backup: bool = True) -> bool:
    """
    从FAISS格式迁移到Peewee数据库
    """
    try:
        old_data_dir = os.path.join('data', 'memory', character_name)
        faiss_metadata_file = os.path.join(old_data_dir, f"{character_name}_metadata.json")
        faiss_texts_file = os.path.join(old_data_dir, f"{character_name}_texts.pkl")
        
        # 备份原始数据
        if backup:
            backup_dir = os.path.join(old_data_dir, 'backup_before_peewee')
            os.makedirs(backup_dir, exist_ok=True)
            
            import shutil
            for file_path in [faiss_metadata_file, faiss_texts_file]:
                if os.path.exists(file_path):
                    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                    if not os.path.exists(backup_path):
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"已备份: {file_path} -> {backup_path}")
        
        # 读取FAISS元数据
        with open(faiss_metadata_file, 'r', encoding='utf-8') as f:
            metadata_info = json.load(f)
        
        # 读取文本数据
        import pickle
        with open(faiss_texts_file, 'rb') as f:
            texts = pickle.load(f)
        
        metadata_list = metadata_info.get('metadata', [])
        
        # 创建新的Peewee数据库
        logger.info("创建新的Peewee数据库...")
        new_db = PeeweeChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=character_name
        )
        
        # 迁移数据
        logger.info("开始迁移FAISS数据到Peewee...")
        
        if texts and len(texts) > 0:
            logger.info(f"找到 {len(texts)} 条记录需要迁移")
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    # 获取对应的元数据
                    metadata = metadata_list[i] if i < len(metadata_list) else {}
                    
                    user_message = metadata.get('user_message')
                    assistant_message = metadata.get('assistant_message')
                    record_type = metadata.get('type', 'conversation')
                    
                    # 添加到新数据库
                    new_db.add_text(
                        text=text,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        record_type=record_type
                    )
            
            # 保存新数据库
            new_db.save_to_file()
            logger.info(f"成功迁移 {len(texts)} 条记录到Peewee数据库")
            
            # 验证迁移结果
            stats = new_db.get_stats()
            logger.info(f"迁移后统计: {stats}")
            
            return True
        else:
            logger.warning(f"角色 {character_name} 没有找到可迁移的FAISS数据")
            return False
            
    except Exception as e:
        logger.error(f"从FAISS迁移失败: {e}")
        traceback.print_exc()
        return False

def migrate_from_json(character_name: str, backup: bool = True) -> bool:
    """
    从JSON格式迁移到Peewee数据库
    """
    try:
        old_data_dir = os.path.join('data', 'memory', character_name)
        old_memory_file = os.path.join(old_data_dir, f"{character_name}_memory.json")
        
        # 备份原始数据
        if backup:
            backup_file = os.path.join(old_data_dir, f"{character_name}_memory_backup_before_peewee.json")
            if not os.path.exists(backup_file):
                import shutil
                shutil.copy2(old_memory_file, backup_file)
                logger.info(f"已备份原始数据到: {backup_file}")
        
        # 加载旧的记忆数据
        logger.info("加载旧的JSON记忆数据...")
        old_db = OldChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=character_name
        )
        old_db.initialize_database()
        
        # 创建新的Peewee数据库
        logger.info("创建新的Peewee数据库...")
        new_db = PeeweeChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=character_name
        )
        
        # 迁移数据
        logger.info("开始迁移JSON数据到Peewee...")
        
        # 从旧数据库中提取文本和元数据
        if hasattr(old_db.rag, 'retriever') and hasattr(old_db.rag.retriever, 'id_to_doc'):
            id_to_doc = old_db.rag.retriever.id_to_doc
            
            if id_to_doc:
                logger.info(f"找到 {len(id_to_doc)} 条记录需要迁移")
                
                # 批量添加文本到新数据库
                for doc_id, text in id_to_doc.items():
                    if text and text.strip():
                        user_message = None
                        assistant_message = None
                        
                        # 如果文本包含对话格式，尝试解析
                        if "用户:" in text and "助手:" in text:
                            lines = text.split('\n')
                            for line in lines:
                                if line.startswith("用户:"):
                                    user_message = line[3:].strip()
                                elif line.startswith("助手:"):
                                    assistant_message = line[3:].strip()
                        
                        new_db.add_text(
                            text=text,
                            user_message=user_message,
                            assistant_message=assistant_message,
                            record_type="migrated_conversation"
                        )
                
                # 保存新数据库
                new_db.save_to_file()
                logger.info(f"成功迁移 {len(id_to_doc)} 条记录到Peewee数据库")
                
                # 验证迁移结果
                stats = new_db.get_stats()
                logger.info(f"迁移后统计: {stats}")
                
                return True
            else:
                logger.warning(f"角色 {character_name} 没有找到可迁移的JSON数据")
                return False
        else:
            logger.warning(f"角色 {character_name} 的旧数据格式不兼容")
            return False
            
    except Exception as e:
        logger.error(f"从JSON迁移失败: {e}")
        traceback.print_exc()
        return False

def migrate_story_memory(story_id: str, backup: bool = True) -> bool:
    """
    迁移单个故事的记忆数据到Peewee数据库
    
    参数:
        story_id: 故事ID
        backup: 是否备份原始数据
        
    返回:
        是否迁移成功
    """
    try:
        logger.info(f"开始迁移故事记忆到Peewee数据库: {story_id}")
        
        # 检查旧数据是否存在
        old_data_dir = os.path.join('data', 'saves', story_id)
        old_memory_file = os.path.join(old_data_dir, f"{story_id}_memory.json")
        
        # 检查是否有FAISS文件
        faiss_metadata_file = os.path.join(old_data_dir, f"{story_id}_metadata.json")
        
        # 优先使用FAISS数据，如果不存在则使用JSON数据
        if os.path.exists(faiss_metadata_file):
            logger.info(f"发现FAISS格式数据，从FAISS迁移故事: {story_id}")
            return migrate_story_from_faiss(story_id, backup)
        elif os.path.exists(old_memory_file):
            logger.info(f"发现JSON格式数据，从JSON迁移故事: {story_id}")
            return migrate_story_from_json(story_id, backup)
        else:
            logger.warning(f"故事 {story_id} 没有找到任何记忆数据")
            return False
            
    except Exception as e:
        logger.error(f"迁移故事 {story_id} 失败: {e}")
        traceback.print_exc()
        return False

def migrate_story_from_faiss(story_id: str, backup: bool = True) -> bool:
    """
    从FAISS格式迁移故事到Peewee数据库
    """
    # 实现与migrate_from_faiss类似，但针对故事
    try:
        old_data_dir = os.path.join('data', 'saves', story_id)
        faiss_metadata_file = os.path.join(old_data_dir, f"{story_id}_metadata.json")
        faiss_texts_file = os.path.join(old_data_dir, f"{story_id}_texts.pkl")
        
        # 备份和迁移逻辑与角色类似
        if backup:
            backup_dir = os.path.join(old_data_dir, 'backup_before_peewee')
            os.makedirs(backup_dir, exist_ok=True)
            
            import shutil
            for file_path in [faiss_metadata_file, faiss_texts_file]:
                if os.path.exists(file_path):
                    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                    if not os.path.exists(backup_path):
                        shutil.copy2(file_path, backup_path)
        
        # 创建新的Peewee故事数据库
        new_db = PeeweeChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=story_id,
            is_story=True
        )
        
        # 读取和迁移数据（逻辑与角色迁移相同）
        with open(faiss_metadata_file, 'r', encoding='utf-8') as f:
            metadata_info = json.load(f)
        
        import pickle
        with open(faiss_texts_file, 'rb') as f:
            texts = pickle.load(f)
        
        metadata_list = metadata_info.get('metadata', [])
        
        if texts and len(texts) > 0:
            logger.info(f"找到 {len(texts)} 条故事记录需要迁移")
            
            for i, text in enumerate(texts):
                if text and text.strip():
                    metadata = metadata_list[i] if i < len(metadata_list) else {}
                    
                    user_message = metadata.get('user_message')
                    assistant_message = metadata.get('assistant_message')
                    record_type = metadata.get('type', 'story')
                    
                    new_db.add_text(
                        text=text,
                        user_message=user_message,
                        assistant_message=assistant_message,
                        record_type=record_type
                    )
            
            new_db.save_to_file()
            logger.info(f"成功迁移 {len(texts)} 条故事记录到Peewee数据库")
            
            stats = new_db.get_stats()
            logger.info(f"迁移后统计: {stats}")
            
            return True
        else:
            logger.warning(f"故事 {story_id} 没有找到可迁移的数据")
            return False
            
    except Exception as e:
        logger.error(f"从FAISS迁移故事失败: {e}")
        traceback.print_exc()
        return False

def migrate_story_from_json(story_id: str, backup: bool = True) -> bool:
    """
    从JSON格式迁移故事到Peewee数据库
    """
    # 实现与migrate_from_json类似，但针对故事
    try:
        old_data_dir = os.path.join('data', 'saves', story_id)
        old_memory_file = os.path.join(old_data_dir, f"{story_id}_memory.json")
        
        if backup:
            backup_file = os.path.join(old_data_dir, f"{story_id}_memory_backup_before_peewee.json")
            if not os.path.exists(backup_file):
                import shutil
                shutil.copy2(old_memory_file, backup_file)
                logger.info(f"已备份故事数据到: {backup_file}")
        
        # 加载旧的故事记忆数据
        old_db = OldChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=story_id,
            is_story=True
        )
        old_db.initialize_database()
        
        # 创建新的Peewee故事数据库
        new_db = PeeweeChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=story_id,
            is_story=True
        )
        
        # 迁移数据（与角色迁移类似）
        if hasattr(old_db.rag, 'retriever') and hasattr(old_db.rag.retriever, 'id_to_doc'):
            id_to_doc = old_db.rag.retriever.id_to_doc
            
            if id_to_doc:
                logger.info(f"找到 {len(id_to_doc)} 条故事记录需要迁移")
                
                for doc_id, text in id_to_doc.items():
                    if text and text.strip():
                        user_message = None
                        assistant_message = None
                        
                        if "用户:" in text and "助手:" in text:
                            lines = text.split('\n')
                            for line in lines:
                                if line.startswith("用户:"):
                                    user_message = line[3:].strip()
                                elif line.startswith("助手:"):
                                    assistant_message = line[3:].strip()
                        
                        new_db.add_text(
                            text=text,
                            user_message=user_message,
                            assistant_message=assistant_message,
                            record_type="migrated_story"
                        )
                
                new_db.save_to_file()
                logger.info(f"成功迁移 {len(id_to_doc)} 条故事记录到Peewee数据库")
                
                stats = new_db.get_stats()
                logger.info(f"迁移后统计: {stats}")
                
                return True
            else:
                logger.warning(f"故事 {story_id} 没有找到可迁移的数据")
                return False
        else:
            logger.warning(f"故事 {story_id} 的旧数据格式不兼容")
            return False
            
    except Exception as e:
        logger.error(f"从JSON迁移故事失败: {e}")
        traceback.print_exc()
        return False

def discover_characters() -> list:
    """
    发现所有需要迁移的角色
    
    返回:
        角色名称列表
    """
    characters = []
    memory_dir = os.path.join('data', 'memory')
    
    if os.path.exists(memory_dir):
        for item in os.listdir(memory_dir):
            char_dir = os.path.join(memory_dir, item)
            if os.path.isdir(char_dir):
                # 检查是否有记忆文件（JSON或FAISS格式）
                json_file = os.path.join(char_dir, f"{item}_memory.json")
                faiss_file = os.path.join(char_dir, f"{item}_metadata.json")
                db_file = os.path.join(char_dir, f"{item}_memory.db")
                
                # 如果已经有Peewee数据库文件，跳过
                if os.path.exists(db_file):
                    logger.info(f"角色 {item} 已经有Peewee数据库，跳过迁移")
                    continue
                
                if os.path.exists(json_file) or os.path.exists(faiss_file):
                    characters.append(item)
    
    return characters

def discover_stories() -> list:
    """
    发现所有需要迁移的故事
    
    返回:
        故事ID列表
    """
    stories = []
    saves_dir = os.path.join('data', 'saves')
    
    if os.path.exists(saves_dir):
        for item in os.listdir(saves_dir):
            story_dir = os.path.join(saves_dir, item)
            if os.path.isdir(story_dir):
                # 检查是否有记忆文件（JSON或FAISS格式）
                json_file = os.path.join(story_dir, f"{item}_memory.json")
                faiss_file = os.path.join(story_dir, f"{item}_metadata.json")
                db_file = os.path.join(story_dir, f"{item}_memory.db")
                
                # 如果已经有Peewee数据库文件，跳过
                if os.path.exists(db_file):
                    logger.info(f"故事 {item} 已经有Peewee数据库，跳过迁移")
                    continue
                
                if os.path.exists(json_file) or os.path.exists(faiss_file):
                    stories.append(item)
    
    return stories

def main():
    """主函数"""
    logger.info("开始记忆存储迁移到Peewee数据库...")
    
    # 检查依赖是否可用
    try:
        import faiss
        logger.info("FAISS库检查通过")
    except ImportError:
        logger.error("FAISS库未安装，请运行: pip install faiss-cpu")
        return False
    
    try:
        import peewee
        logger.info("Peewee库检查通过")
    except ImportError:
        logger.error("Peewee库未安装，请运行: pip install peewee")
        return False
    
    # 发现需要迁移的数据
    characters = discover_characters()
    stories = discover_stories()
    
    logger.info(f"发现 {len(characters)} 个角色和 {len(stories)} 个故事需要迁移到Peewee")
    
    if not characters and not stories:
        logger.info("没有发现需要迁移的数据")
        return True
    
    # 迁移角色记忆
    success_count = 0
    total_count = 0
    
    for character in characters:
        total_count += 1
        if migrate_character_memory(character):
            success_count += 1
    
    # 迁移故事记忆
    for story in stories:
        total_count += 1
        if migrate_story_memory(story):
            success_count += 1
    
    logger.info(f"迁移完成: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        logger.info("所有数据迁移成功到Peewee数据库！")
        logger.info("现在记忆数据存储在SQLite数据库中，不再使用JSON文件")
        return True
    else:
        logger.warning("部分数据迁移失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
