#!/usr/bin/env python3
"""
音频文件清理工具
用于清理过期的TTS音频文件
"""
import os
import sys
import time
import argparse
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.tts_service import get_tts_service

def cleanup_audio_files(max_age_hours=24, dry_run=False):
    """
    清理过期的音频文件
    
    Args:
        max_age_hours: 文件最大保留时间（小时）
        dry_run: 是否只是预览，不实际删除
    """
    try:
        # 初始化配置服务
        from services.config_service import config_service
        if not config_service.initialize():
            print("配置初始化失败")
            return
        
        tts_service = get_tts_service()
        audio_dir = tts_service.audio_dir
        
        if not audio_dir.exists():
            print(f"音频目录不存在: {audio_dir}")
            return
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        deleted_count = 0
        total_size = 0
        
        print(f"扫描音频目录: {audio_dir}")
        print(f"删除超过 {max_age_hours} 小时的文件")
        print(f"预览模式: {'是' if dry_run else '否'}")
        print("-" * 50)
        
        for audio_file in audio_dir.glob("tts_*.mp3"):
            file_age = current_time - audio_file.stat().st_mtime
            file_size = audio_file.stat().st_size
            
            if file_age > max_age_seconds:
                age_hours = file_age / 3600
                size_mb = file_size / (1024 * 1024)
                
                print(f"{'[预览]' if dry_run else '[删除]'} {audio_file.name} "
                      f"(年龄: {age_hours:.1f}小时, 大小: {size_mb:.2f}MB)")
                
                if not dry_run:
                    audio_file.unlink()
                
                deleted_count += 1
                total_size += file_size
        
        total_size_mb = total_size / (1024 * 1024)
        
        print("-" * 50)
        print(f"{'预计' if dry_run else '实际'}删除文件数: {deleted_count}")
        print(f"{'预计' if dry_run else '实际'}释放空间: {total_size_mb:.2f}MB")
        
        if dry_run and deleted_count > 0:
            print("\n使用 --execute 参数执行实际删除")
        
    except Exception as e:
        print(f"清理失败: {e}")

def get_audio_stats():
    """获取音频目录统计信息"""
    try:
        # 初始化配置服务
        from services.config_service import config_service
        if not config_service.initialize():
            print("配置初始化失败")
            return
        
        tts_service = get_tts_service()
        audio_dir = tts_service.audio_dir
        
        if not audio_dir.exists():
            print(f"音频目录不存在: {audio_dir}")
            return
        
        audio_files = list(audio_dir.glob("tts_*.mp3"))
        total_count = len(audio_files)
        total_size = sum(f.stat().st_size for f in audio_files)
        total_size_mb = total_size / (1024 * 1024)
        
        print(f"音频目录: {audio_dir}")
        print(f"音频文件数量: {total_count}")
        print(f"总占用空间: {total_size_mb:.2f}MB")
        
        if total_count > 0:
            current_time = time.time()
            ages = [(current_time - f.stat().st_mtime) / 3600 for f in audio_files]
            avg_age = sum(ages) / len(ages)
            oldest_age = max(ages)
            newest_age = min(ages)
            
            print(f"平均文件年龄: {avg_age:.1f}小时")
            print(f"最旧文件年龄: {oldest_age:.1f}小时")
            print(f"最新文件年龄: {newest_age:.1f}小时")
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="TTS音频文件清理工具")
    parser.add_argument("--max-age", type=int, default=24, 
                       help="文件最大保留时间（小时），默认24小时")
    parser.add_argument("--execute", action="store_true", 
                       help="执行实际删除（默认为预览模式）")
    parser.add_argument("--stats", action="store_true", 
                       help="显示音频目录统计信息")
    
    args = parser.parse_args()
    
    if args.stats:
        get_audio_stats()
    else:
        cleanup_audio_files(args.max_age, not args.execute)

if __name__ == "__main__":
    main()