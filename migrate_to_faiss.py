#!/usr/bin/env python3
"""
记忆存储迁移脚本
从JSON格式迁移到FAISS格式
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
from utils.faiss_memory_utils import FaissChatHistoryVectorDB
from utils.memory_utils import ChatHistoryVectorDB as OldChatHistoryVectorDB

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Migration")

def migrate_character_memory(character_name: str, backup: bool = True) -> bool:
    """
    迁移单个角色的记忆数据
    
    参数:
        character_name: 角色名称
        backup: 是否备份原始数据
        
    返回:
        是否迁移成功
    """
    try:
        logger.info(f"开始迁移角色记忆: {character_name}")
        
        # 检查旧数据是否存在
        old_data_dir = os.path.join('data', 'memory', character_name)
        old_memory_file = os.path.join(old_data_dir, f"{character_name}_memory.json")
        
        if not os.path.exists(old_memory_file):
            logger.warning(f"角色 {character_name} 的旧记忆文件不存在: {old_memory_file}")
            return False
        
        # 备份原始数据
        if backup:
            backup_file = os.path.join(old_data_dir, f"{character_name}_memory_backup.json")
            if not os.path.exists(backup_file):
                import shutil
                shutil.copy2(old_memory_file, backup_file)
                logger.info(f"已备份原始数据到: {backup_file}")
        
        # 加载旧的记忆数据
        logger.info("加载旧的记忆数据...")
        old_db = OldChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=character_name
        )
        old_db.initialize_database()
        
        # 创建新的FAISS数据库
        logger.info("创建新的FAISS数据库...")
        new_db = FaissChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=character_name
        )
        
        # 迁移数据
        logger.info("开始迁移数据...")
        
        # 从旧数据库中提取文本和元数据
        if hasattr(old_db.rag, 'retriever') and hasattr(old_db.rag.retriever, 'id_to_doc'):
            id_to_doc = old_db.rag.retriever.id_to_doc
            
            if id_to_doc:
                logger.info(f"找到 {len(id_to_doc)} 条记录需要迁移")
                
                # 批量添加文本到新数据库
                for doc_id, text in id_to_doc.items():
                    if text and text.strip():
                        # 尝试解析对话格式
                        metadata = {
                            "timestamp": "migrated",
                            "doc_id": doc_id,
                            "type": "migrated_conversation"
                        }
                        
                        # 如果文本包含对话格式，尝试解析
                        if "用户:" in text and "助手:" in text:
                            lines = text.split('\n')
                            user_msg = ""
                            assistant_msg = ""
                            
                            for line in lines:
                                if line.startswith("用户:"):
                                    user_msg = line[3:].strip()
                                elif line.startswith("助手:"):
                                    assistant_msg = line[3:].strip()
                            
                            if user_msg and assistant_msg:
                                metadata.update({
                                    "user_message": user_msg,
                                    "assistant_message": assistant_msg
                                })
                        
                        new_db.add_text(text, metadata)
                
                # 保存新数据库
                new_db.save_to_file()
                logger.info(f"成功迁移 {len(id_to_doc)} 条记录到FAISS数据库")
                
                # 验证迁移结果
                stats = new_db.get_stats()
                logger.info(f"迁移后统计: {stats}")
                
                return True
            else:
                logger.warning(f"角色 {character_name} 没有找到可迁移的数据")
                return False
        else:
            logger.warning(f"角色 {character_name} 的旧数据格式不兼容")
            return False
            
    except Exception as e:
        logger.error(f"迁移角色 {character_name} 失败: {e}")
        traceback.print_exc()
        return False

def migrate_story_memory(story_id: str, backup: bool = True) -> bool:
    """
    迁移单个故事的记忆数据
    
    参数:
        story_id: 故事ID
        backup: 是否备份原始数据
        
    返回:
        是否迁移成功
    """
    try:
        logger.info(f"开始迁移故事记忆: {story_id}")
        
        # 检查旧数据是否存在
        old_data_dir = os.path.join('data', 'saves', story_id)
        old_memory_file = os.path.join(old_data_dir, f"{story_id}_memory.json")
        
        if not os.path.exists(old_memory_file):
            logger.warning(f"故事 {story_id} 的旧记忆文件不存在: {old_memory_file}")
            return False
        
        # 备份原始数据
        if backup:
            backup_file = os.path.join(old_data_dir, f"{story_id}_memory_backup.json")
            if not os.path.exists(backup_file):
                import shutil
                shutil.copy2(old_memory_file, backup_file)
                logger.info(f"已备份原始数据到: {backup_file}")
        
        # 加载旧的记忆数据
        logger.info("加载旧的故事记忆数据...")
        old_db = OldChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=story_id,
            is_story=True
        )
        old_db.initialize_database()
        
        # 创建新的FAISS数据库
        logger.info("创建新的FAISS故事数据库...")
        new_db = FaissChatHistoryVectorDB(
            RAG_config=get_RAG_config(),
            character_name=story_id,
            is_story=True
        )
        
        # 迁移数据（与角色迁移类似）
        logger.info("开始迁移故事数据...")
        
        if hasattr(old_db.rag, 'retriever') and hasattr(old_db.rag.retriever, 'id_to_doc'):
            id_to_doc = old_db.rag.retriever.id_to_doc
            
            if id_to_doc:
                logger.info(f"找到 {len(id_to_doc)} 条故事记录需要迁移")
                
                for doc_id, text in id_to_doc.items():
                    if text and text.strip():
                        metadata = {
                            "timestamp": "migrated",
                            "doc_id": doc_id,
                            "type": "migrated_story"
                        }
                        
                        if "用户:" in text and "助手:" in text:
                            lines = text.split('\n')
                            user_msg = ""
                            assistant_msg = ""
                            
                            for line in lines:
                                if line.startswith("用户:"):
                                    user_msg = line[3:].strip()
                                elif line.startswith("助手:"):
                                    assistant_msg = line[3:].strip()
                            
                            if user_msg and assistant_msg:
                                metadata.update({
                                    "user_message": user_msg,
                                    "assistant_message": assistant_msg
                                })
                        
                        new_db.add_text(text, metadata)
                
                new_db.save_to_file()
                logger.info(f"成功迁移 {len(id_to_doc)} 条故事记录到FAISS数据库")
                
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
        logger.error(f"迁移故事 {story_id} 失败: {e}")
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
                memory_file = os.path.join(char_dir, f"{item}_memory.json")
                if os.path.exists(memory_file):
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
                memory_file = os.path.join(story_dir, f"{item}_memory.json")
                if os.path.exists(memory_file):
                    stories.append(item)
    
    return stories

def main():
    """主函数"""
    logger.info("开始记忆存储迁移...")
    
    # 检查FAISS是否可用
    try:
        import faiss
        logger.info("FAISS库检查通过")
    except ImportError:
        logger.error("FAISS库未安装，请运行: pip install faiss-cpu")
        return False
    
    # 发现需要迁移的数据
    characters = discover_characters()
    stories = discover_stories()
    
    logger.info(f"发现 {len(characters)} 个角色和 {len(stories)} 个故事需要迁移")
    
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
        logger.info("所有数据迁移成功！")
        logger.info("现在可以安全地删除旧的JSON记忆文件（建议保留备份）")
        return True
    else:
        logger.warning("部分数据迁移失败，请检查日志")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
