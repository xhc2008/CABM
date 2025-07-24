/**
 * 流式响应处理器
 * 参考 stream.py 的处理方式，在前端实现流式数据的分段和控制
 */

// 常量配置
const OUTPUT_DELAY = 20; // 每个字符的输出间隔（毫秒）
const END_MARKER = "<END>"; // 结束标记符号
const PAUSE_MARKERS = ['。', '？', '！', '…', '~']; // 暂停输出的分隔符号

class StreamProcessor {
    constructor() {
        this.buffer = [];
        this.active = true;
        this.isPaused = false;
        this.currentParagraph = '';
        this.paragraphs = [];
        this.onCharacterCallback = null;
        this.onPauseCallback = null;
        this.onCompleteCallback = null;
        this.processingTimeout = null;
    }

    /**
     * 设置回调函数
     */
    setCallbacks(onCharacter, onPause, onComplete) {
        this.onCharacterCallback = onCharacter;
        this.onPauseCallback = onPause;
        this.onCompleteCallback = onComplete;
    }

    /**
     * 添加数据到缓冲区
     */
    addData(data) {
        // 将数据逐字符添加到缓冲区
        for (const char of data) {
            this.buffer.push(char);
        }
        
        // 如果没有在处理且没有暂停，开始处理
        if (!this.processingTimeout && this.active && !this.isPaused) {
            this.processBuffer();
        }
    }

    /**
     * 标记数据结束
     */
    markEnd() {
        this.buffer.push(END_MARKER);
        this.active = false;
        
        // 如果没有在处理，开始处理
        if (!this.processingTimeout) {
            this.processBuffer();
        }
    }

    /**
     * 处理缓冲区数据
     */
    processBuffer() {
        if (this.buffer.length === 0 || this.processingTimeout) {
            return;
        }

        // 如果暂停，等待继续
        if (this.isPaused) {
            this.processingTimeout = setTimeout(() => {
                this.processingTimeout = null;
                this.processBuffer();
            }, 100);
            return;
        }

        // 取出一个字符
        const char = this.buffer.shift();

        // 如果是结束标记
        if (char === END_MARKER) {
            // 如果还有未处理的段落，添加到结果中
            if (this.currentParagraph) {
                this.paragraphs.push(this.currentParagraph);
                this.currentParagraph = '';
            }
            
            // 调用完成回调
            if (this.onCompleteCallback) {
                this.onCompleteCallback(this.paragraphs.join(''));
            }
            return;
        }

        // 输出当前字符
        this.currentParagraph += char;
        
        // 调用字符回调
        if (this.onCharacterCallback) {
            this.onCharacterCallback(this.paragraphs.join('') + this.currentParagraph);
        }

        // 检查下一个字符是否是结束标记
        const nextChar = this.buffer.length > 0 ? this.buffer[0] : null;

        // 只有在下一个字符不是结束标记时才检查暂停
        if (PAUSE_MARKERS.includes(char) && nextChar !== END_MARKER) {
            this.handlePause();
        } else {
            // 继续处理下一个字符
            this.processingTimeout = setTimeout(() => {
                this.processingTimeout = null;
                this.processBuffer();
            }, OUTPUT_DELAY);
        }
    }

    /**
     * 处理暂停状态
     */
    handlePause() {
        this.isPaused = true;
        
        // 将当前段落添加到段落列表
        if (this.currentParagraph) {
            this.paragraphs.push(this.currentParagraph);
            this.currentParagraph = '';
        }
        
        // 调用暂停回调
        if (this.onPauseCallback) {
            this.onPauseCallback(this.paragraphs.join(''));
        }
    }

    /**
     * 继续处理
     */
    continue() {
        if (this.isPaused) {
            this.isPaused = false;
            
            // 继续处理缓冲区
            if (!this.processingTimeout) {
                this.processBuffer();
            }
        }
    }

    /**
     * 跳过当前处理，直接显示所有内容
     */
    skip() {
        // 清除处理超时
        if (this.processingTimeout) {
            clearTimeout(this.processingTimeout);
            this.processingTimeout = null;
        }

        // 将所有缓冲区内容添加到当前段落
        let remainingContent = '';
        while (this.buffer.length > 0) {
            const char = this.buffer.shift();
            if (char === END_MARKER) {
                break;
            }
            remainingContent += char;
        }

        this.currentParagraph += remainingContent;
        
        // 如果有内容，添加到段落列表
        if (this.currentParagraph) {
            this.paragraphs.push(this.currentParagraph);
            this.currentParagraph = '';
        }

        // 调用完成回调
        if (this.onCompleteCallback) {
            this.onCompleteCallback(this.paragraphs.join(''));
        }

        // 重置状态
        this.isPaused = false;
        this.active = false;
    }

    /**
     * 重置处理器状态
     */
    reset() {
        // 清除处理超时
        if (this.processingTimeout) {
            clearTimeout(this.processingTimeout);
            this.processingTimeout = null;
        }

        this.buffer = [];
        this.active = true;
        this.isPaused = false;
        this.currentParagraph = '';
        this.paragraphs = [];
    }

    /**
     * 获取当前完整内容
     */
    getFullContent() {
        return this.paragraphs.join('') + this.currentParagraph;
    }

    /**
     * 检查是否正在处理
     */
    isProcessing() {
        return this.active || this.buffer.length > 0 || this.processingTimeout !== null;
    }
}

// 导出类
window.StreamProcessor = StreamProcessor;