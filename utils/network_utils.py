"""
网络工具函数
用于获取本地IP地址等网络相关功能
"""
import socket
import subprocess
import re
from typing import Optional, List

def get_local_ip() -> Optional[str]:
    """
    获取本地IP地址（优先返回192.168开头的地址）
    
    Returns:
        str: 本地IP地址，如果获取失败返回None
    """
    try:
        # 方法1: 通过连接外部地址获取本地IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # 连接到一个外部地址（不会实际发送数据）
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172."):
                return ip
    except Exception:
        pass
    
    try:
        # 方法2: 获取所有网络接口的IP地址
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        
        # 优先返回192.168开头的地址
        for ip in ip_list:
            if ip.startswith("192.168."):
                return ip
        
        # 其次返回10.开头的地址
        for ip in ip_list:
            if ip.startswith("10."):
                return ip
        
        # 最后返回172.16-31开头的地址
        for ip in ip_list:
            if ip.startswith("172."):
                parts = ip.split(".")
                if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                    return ip
        
        # 如果没有私有IP，返回第一个非回环地址
        for ip in ip_list:
            if not ip.startswith("127."):
                return ip
                
    except Exception:
        pass
    
    try:
        # 方法3: 在Windows上使用ipconfig命令
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            # 查找IPv4地址
            lines = result.stdout.split('\n')
            for line in lines:
                if 'IPv4' in line and '192.168.' in line:
                    # 提取IP地址
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
    except Exception:
        pass
    
    # 如果所有方法都失败，返回localhost
    return "127.0.0.1"

def get_all_local_ips() -> List[str]:
    """
    获取所有本地IP地址
    
    Returns:
        List[str]: 所有本地IP地址列表
    """
    ips = []
    
    try:
        hostname = socket.gethostname()
        ip_list = socket.gethostbyname_ex(hostname)[2]
        
        for ip in ip_list:
            if not ip.startswith("127."):  # 排除回环地址
                ips.append(ip)
                
    except Exception:
        pass
    
    # 如果没有找到任何IP，至少返回localhost
    if not ips:
        ips.append("127.0.0.1")
    
    return ips

def is_port_available(host: str, port: int) -> bool:
    """
    检查端口是否可用
    
    Args:
        host: 主机地址
        port: 端口号
        
    Returns:
        bool: 端口是否可用
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # 如果连接失败，说明端口可用
    except Exception:
        return False

if __name__ == "__main__":
    # 测试函数
    print("本地IP地址:", get_local_ip())
    print("所有本地IP地址:", get_all_local_ips())
    print("端口5000是否可用:", is_port_available("127.0.0.1", 5000))