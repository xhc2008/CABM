#!/usr/bin/env python3
"""
角色详细信息向量数据库构建测试程序
用法：python build_details.py <角色ID> <文件名.txt>
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def test_build_character_details(character_id, filename):
    """
    测试构建角色详细信息向量数据库
    
    Args:
        character_id: 角色ID
        filename: 文本文件名（与测试程序同目录）
    """
    try:
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
        return False

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python build_details.py <角色ID> <文件名.txt>")
        print("示例: python build_details.py 123 character_background.txt")
        sys.exit(1)
    
    character_id = sys.argv[1]
    filename = sys.argv[2]
    
    print(f"开始测试角色详细信息向量数据库构建...")
    print(f"角色ID: {character_id}")
    print(f"文件: {filename}")
    print("-" * 50)
    
    success = test_build_character_details(character_id, filename)
    
    if success:
        print("\n测试完成 ✓")
        sys.exit(0)
    else:
        print("\n测试失败 ✗")
        sys.exit(1)

if __name__ == "__main__":
    main()