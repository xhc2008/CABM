import queue
import threading
import time
import sys
import msvcrt  # Windows平台下的按键检测
import random
import os

# 常量配置
OUTPUT_DELAY = 0.05  # 每个字符的输出间隔（秒）
END_MARKER = "<END>"  # 结束标记符号
PAUSE_MARKERS = {'。', '？', '！'}  # 暂停输出的分隔符号

class StreamProcessor:
    def __init__(self):
        self.buffer = queue.Queue()
        self.active = True
    
    def start_producer(self, stream_data):
        """生产者线程：将流式数据逐字放入队列"""
        def _producer():
            for chunk in stream_data:
                for char in chunk:  # 将每个字符单独放入队列
                    self.buffer.put(char)
                    time.sleep(0.01)  # 模拟AI响应延迟
            self.buffer.put(END_MARKER)
            self.active = False
        
        threading.Thread(target=_producer, daemon=True).start()
    
    def start_consumer(self):
        """消费者线程：从队列中取出字符并按规定输出"""
        def _consumer():
            while self.active or not self.buffer.empty():
                try:
                    # 从队列中获取字符（带超时防止永久阻塞）
                    char = self.buffer.get(timeout=0.1)
                    
                    if char == END_MARKER:
                        print("\n")  # 结束时不暂停，直接换行
                        return  # 遇到结束标记则退出
                    
                    # 输出当前字符
                    sys.stdout.write(char)
                    sys.stdout.flush()
                    time.sleep(OUTPUT_DELAY)  # 控制输出速度
                    
                    # 检查下一个字符是否是结束标记
                    next_char = None
                    if not self.buffer.empty():
                        next_char = self.buffer.queue[0]  # 查看但不取出下一个字符
                    
                    # 只有在下一个字符不是结束标记时才暂停
                    if char in PAUSE_MARKERS and next_char != END_MARKER:
                        self.handle_pause()
                
                except queue.Empty:
                    # 等待更多数据的到来
                    continue
        
        threading.Thread(target=_consumer).start()
    
    def handle_pause(self):
        """处理暂停状态（等待用户按键）"""
        sys.stdout.write("\n按下任意键继续...")
        sys.stdout.flush()
        self.wait_for_keypress()
        os.system("cls")
    
    def wait_for_keypress(self):
        """等待用户按下任意键（Windows平台）"""
        while not msvcrt.kbhit():
            time.sleep(0.1)
        msvcrt.getch()  # 清除按键缓冲区

def simulate_ai_stream(text):
    """模拟AI流式响应生成器，每次可能返回1-5个字符"""
    index = 0
    length = len(text)
    while index < length:
        # 随机决定这次返回多少个字符（1-5个）
        chunk_size = random.randint(1, 5)
        chunk = text[index:index+chunk_size]
        yield chunk
        time.sleep(random.uniform(0, 0.20))  # 模拟响应延迟
        index += chunk_size

if __name__ == "__main__":
    while True:
        userinput = input("请输入您的问题：")
        os.system("cls")
        # 模拟的AI响应文本（实际应用中替换为真实的流式响应）
        ai_response = "你好！这是一个流式响应示例。它将逐字显示，并在标点处暂停。你可以随时继续查看后续内容。准备好开始了吗？让我们开始吧！"
        
        processor = StreamProcessor()
        
        # 启动生产者线程（处理流式输入）
        processor.start_producer(simulate_ai_stream(ai_response))
        
        # 启动消费者线程（处理输出）
        processor.start_consumer()
        
        # 等待消费者线程完成
        while processor.active or not processor.buffer.empty():
            time.sleep(0.1)