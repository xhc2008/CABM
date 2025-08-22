#!/usr/bin/env python3
"""
角色详细信息向量数据库构建工具
用法：
  python build_details.py <角色ID> <文件名.txt>           # 从文本文件构建
  python build_details.py --list                        # 列出所有可用角色
  python build_details.py --search <角色ID> <查询文本>   # 测试搜索功能
  python build_details.py --stats <角色ID>              # 查看角色详细信息统计
"""

import sys
import tempfile
import os
import rtoml
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def get_available_characters():
    """获取所有可用的角色列表"""
    characters = []
    characters_dir = Path("characters")
    
    if characters_dir.exists():
        for toml_file in characters_dir.glob("*.toml"):
            try:
                with open(toml_file, 'r', encoding='utf-8') as f:
                    char_data = rtoml.load(f)
                    characters.append({
                        'id': char_data.get('id', toml_file.stem),
                        'name': char_data.get('name', toml_file.stem),
                        'name_en': char_data.get('name_en', ''),
                        'description': char_data.get('description', '').strip()
                    })
            except Exception as e:
                print(f"警告：无法读取角色配置文件 {toml_file}: {e}")
    
    return characters

def list_characters():
    """列出所有可用角色"""
    characters = get_available_characters()
    
    if not characters:
        print("未找到任何角色配置文件")
        return
    
    print("可用角色列表：")
    print("-" * 60)
    for char in characters:
        print(f"ID: {char['id']}")
        print(f"名称: {char['name']} ({char['name_en']})")
        if char['description']:
            print(f"描述: {char['description']}")
        
        # 检查是否已有详细信息数据库
        details_file = Path(f"data/details/{char['id']}.json")
        if details_file.exists():
            print("状态: ✓ 已有详细信息数据库")
        else:
            print("状态: ✗ 未构建详细信息数据库")
        print("-" * 60)

def validate_character_id(character_id):
    """验证角色ID是否有效"""
    characters = get_available_characters()
    valid_ids = [char['id'] for char in characters]
    
    if character_id not in valid_ids:
        print(f"错误：角色ID '{character_id}' 不存在")
        print(f"可用的角色ID: {', '.join(valid_ids)}")
        print("使用 'python build_details.py --list' 查看所有角色")
        return False
    
    return True

def test_build_character_details(character_id, filename):
    """
    测试构建角色详细信息向量数据库
    
    Args:
        character_id: 角色ID
        filename: 文本文件名（与测试程序同目录）
    """
    try:
        # 验证角色ID
        if not validate_character_id(character_id):
            return False
        
        # 导入相关服务
        from services.character_details_service import CharacterDetailsService
        
        # 创建服务实例
        character_details_service = CharacterDetailsService()
        
        # 检查文件是否存在
        file_path = Path(filename)
        if not file_path.exists():
            print(f"错误：文件 '{filename}' 不存在")
            return False
        
        if not file_path.suffix.lower() == '.txt':
            print(f"错误：文件 '{filename}' 不是文本文件(.txt)")
            return False
        
        # 检查文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                print(f"错误：文件 '{filename}' 为空")
                return False
        except UnicodeDecodeError:
            print(f"错误：文件 '{filename}' 编码不是UTF-8")
            return False
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # 复制文件到临时目录（保持原始文件名）
            temp_file_path = temp_dir_path / file_path.name
            with open(file_path, 'rb') as src, open(temp_file_path, 'wb') as dst:
                dst.write(src.read())
            
            # 构建角色详细信息向量数据库
            success = character_details_service.build_character_details(
                character_id, [str(temp_file_path)]
            )
            
            if success:
                print(f"✓ 角色详细信息数据库构建成功: 角色ID={character_id}, 文件={filename}")
                
                # 显示构建后的统计信息
                stats = character_details_service.get_character_details_stats(character_id)
                print(f"数据库文件: {stats.get('database_file', '未知')}")
                return True
            else:
                print(f"✗ 角色详细信息数据库构建失败: 角色ID={character_id}, 文件={filename}")
                return False
                
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保项目依赖已安装且路径正确")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_character_details(character_id, query):
    """
    测试搜索角色详细信息
    
    Args:
        character_id: 角色ID
        query: 查询文本
    """
    try:
        # 验证角色ID
        if not validate_character_id(character_id):
            return False
        
        # 检查详细信息数据库是否存在
        details_file = Path(f"data/details/{character_id}.json")
        if not details_file.exists():
            print(f"错误：角色 '{character_id}' 的详细信息数据库不存在")
            print(f"请先使用以下命令构建数据库：")
            print(f"python build_details.py {character_id} <文本文件.txt>")
            return False
        
        # 导入相关服务
        from services.character_details_service import CharacterDetailsService
        
        # 创建服务实例
        character_details_service = CharacterDetailsService()
        
        # 执行搜索
        print(f"正在搜索角色 '{character_id}' 的详细信息...")
        print(f"查询: '{query}'")
        print("-" * 50)
        
        result = character_details_service.search_character_details(character_id, query, top_k=3)
        
        if result:
            print("搜索结果:")
            print(result)
        else:
            print("未找到相关信息")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保项目依赖已安装且路径正确")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_character_stats(character_id):
    """
    显示角色详细信息统计
    
    Args:
        character_id: 角色ID
    """
    try:
        # 验证角色ID
        if not validate_character_id(character_id):
            return False
        
        # 导入相关服务
        from services.character_details_service import CharacterDetailsService
        
        # 创建服务实例
        character_details_service = CharacterDetailsService()
        
        # 获取统计信息
        stats = character_details_service.get_character_details_stats(character_id)
        
        print(f"角色 '{character_id}' 详细信息统计:")
        print("-" * 40)
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保项目依赖已安装且路径正确")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("角色详细信息向量数据库构建工具")
        print("用法：")
        print("  python build_details.py <角色ID> <文件名.txt>           # 从文本文件构建")
        print("  python build_details.py --list                        # 列出所有可用角色")
        print("  python build_details.py --search <角色ID> <查询文本>   # 测试搜索功能")
        print("  python build_details.py --stats <角色ID>              # 查看角色详细信息统计")
        print()
        print("示例：")
        print("  python build_details.py Collei character_background.txt")
        print("  python build_details.py --list")
        print("  python build_details.py --search Collei 性格特点")
        print("  python build_details.py --stats Collei")
        sys.exit(1)
    
    # 处理不同的命令
    if sys.argv[1] == "--list":
        list_characters()
        sys.exit(0)
    
    elif sys.argv[1] == "--search":
        if len(sys.argv) != 4:
            print("错误：搜索命令需要角色ID和查询文本")
            print("用法: python build_details.py --search <角色ID> <查询文本>")
            sys.exit(1)
        
        character_id = sys.argv[2]
        query = sys.argv[3]
        
        success = test_search_character_details(character_id, query)
        sys.exit(0 if success else 1)
    
    elif sys.argv[1] == "--stats":
        if len(sys.argv) != 3:
            print("错误：统计命令需要角色ID")
            print("用法: python build_details.py --stats <角色ID>")
            sys.exit(1)
        
        character_id = sys.argv[2]
        success = show_character_stats(character_id)
        sys.exit(0 if success else 1)
    
    else:
        # 构建数据库模式
        if len(sys.argv) != 3:
            print("错误：构建命令需要角色ID和文件名")
            print("用法: python build_details.py <角色ID> <文件名.txt>")
            print("示例: python build_details.py Collei character_background.txt")
            sys.exit(1)
        
        character_id = sys.argv[1]
        filename = sys.argv[2]
        
        print(f"开始构建角色详细信息向量数据库...")
        print(f"角色ID: {character_id}")
        print(f"文件: {filename}")
        print("-" * 50)
        
        success = test_build_character_details(character_id, filename)
        
        if success:
            print("\n构建完成 ✓")
            print(f"可以使用以下命令测试搜索功能：")
            print(f"python build_details.py --search {character_id} \"查询文本\"")
            sys.exit(0)
        else:
            print("\n构建失败 ✗")
            sys.exit(1)

if __name__ == "__main__":
    main()
