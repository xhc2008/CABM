/**
 * StreamHandler - 处理AI响应的类
 * 实现了接收非流式响应、打字机效果和分段显示功能
 */
class StreamHandler {
    /**
     * 创建一个新的StreamHandler实例
     * @param {Object} config - 配置选项
     */
    constructor(config = {}) {
        // 默认配置
        this.config = {
            paragraphDelimiters: ["。", "！", "？", ".", "!", "?"], // 段落分隔符
            endToken: "[DONE]",                                   // 结束标记
            maxParagraphLength: 200,                              // 最大段落长度
            typingSpeed: 10                                       // 打字速度(毫秒/字符)
        };

        // 合并用户配置
        if (config) {
            this.config = { ...this.config, ...config };
        }

        // 状态管理
        this.fullResponse = "";      // 完整响应
        this.segments = [];          // 已完成的段落
        this.currentPosition = 0;    // 当前处理位置
        this.currentSegmentStart = 0; // 当前段落起始位置
        this.currentSegmentIndex = 0; // 当前段落索引
        this.isPaused = false;       // 是否暂停
        this.isComplete = false;     // 是否完成
        this.typingTimer = null;     // 打字定时器

        // 回调函数
        this.onSegmentComplete = null;  // 段落完成回调
        this.onContentUpdate = null;    // 内容更新回调
        this.onResponseComplete = null; // 响应完成回调
    }

    /**
     * 重置处理器状态
     */
    reset() {
        this.fullResponse = "";
        this.segments = [];
        this.currentPosition = 0;
        this.currentSegmentStart = 0;
        this.currentSegmentIndex = 0;
        this.isPaused = false;
        this.isComplete = false;

        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }
    }

    /**
     * 开始接收响应
     * @param {ReadableStream} stream - 响应流
     */
    async startReceiving(stream) {
        this.reset();

        try {
            const reader = stream.getReader();
            const decoder = new TextDecoder();
            let responseText = "";

            // 读取流数据
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                // 解码数据块
                const chunk = decoder.decode(value, { stream: true });
                responseText += chunk;
            }

            // 处理完整响应
            this._processFullResponse(responseText);
            
            // 开始打字效果
            this._startTyping();
        } catch (error) {
            console.error("处理错误:", error);
            this._handleComplete();
        }
    }

    /**
     * 处理完整响应
     * @private
     * @param {string} responseText - 完整响应文本
     */
    _processFullResponse(responseText) {
        const lines = responseText.split('\n');
        let content = "";

        for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine) continue;

            if (trimmedLine.startsWith('data: ')) {
                const dataStr = trimmedLine.substring(6);

                // 检查是否是结束标记
                if (dataStr === this.config.endToken) {
                    continue;
                }

                try {
                    // 尝试解析JSON数据
                    const data = JSON.parse(dataStr);
                    
                    // 处理流控制信息
                    if (data.stream_control) {
                        const control = data.stream_control;
                        
                        if (control.paragraph) {
                            content += control.paragraph;
                        } else if (control.content) {
                            content += control.content;
                        }
                    }
                    // 处理标准OpenAI格式
                    else if (data.choices && data.choices.length > 0) {
                        const delta = data.choices[0].delta || {};
                        if (delta.content) {
                            content += delta.content;
                        }
                    }
                    // 处理直接内容字段
                    else if (data.content) {
                        content += data.content;
                    }
                } catch (error) {
                    // 如果不是JSON，直接作为内容处理
                    if (dataStr && dataStr !== "[DONE]") {
                        content += dataStr;
                    }
                }
            } else if (trimmedLine) {
                // 非data前缀的行，直接作为内容处理
                content += trimmedLine;
            }
        }

        this.fullResponse = content;
    }

    /**
     * 开始打字效果
     * @private
     */
    _startTyping() {
        if (this.isComplete || this.fullResponse.length === 0) {
            this._handleComplete();
            return;
        }

        this.typingTimer = setTimeout(() => {
            this._typeNextChar();
        }, this.config.typingSpeed);
    }

    /**
     * 输出下一个字符
     * @private
     */
    _typeNextChar() {
        // 如果暂停或已完成，不继续
        if (this.isPaused || this.isComplete) {
            return;
        }

        // 如果已经处理完所有字符
        if (this.currentPosition >= this.fullResponse.length) {
            // 处理最后一个段落
            if (this.currentPosition > this.currentSegmentStart) {
                this._completeCurrentSegment();
            }
            
            this._handleComplete();
            return;
        }

        // 获取当前字符
        const currentChar = this.fullResponse[this.currentPosition];
        this.currentPosition++;

        // 更新显示内容
        if (this.onContentUpdate) {
            this.onContentUpdate(this.fullResponse.substring(0, this.currentPosition));
        }

        // 检查是否需要分段
        if (this._shouldSegmentParagraph()) {
            this._completeCurrentSegment();
            return; // 暂停，等待用户继续
        }

        // 继续处理下一个字符
        this.typingTimer = setTimeout(() => {
            this._typeNextChar();
        }, this.config.typingSpeed);
    }

    /**
     * 检查是否需要分段
     * @private
     * @returns {boolean} 是否需要分段
     */
    _shouldSegmentParagraph() {
        // 检查分隔符
        for (const delimiter of this.config.paragraphDelimiters) {
            if (this.currentPosition >= delimiter.length && 
                this.fullResponse.substring(this.currentPosition - delimiter.length, this.currentPosition) === delimiter) {
                return true;
            }
        }

        // 检查段落长度
        if (this.currentPosition - this.currentSegmentStart >= this.config.maxParagraphLength) {
            return true;
        }

        return false;
    }

    /**
     * 完成当前段落
     * @private
     */
    _completeCurrentSegment() {
        // 获取当前段落内容
        const segment = this.fullResponse.substring(this.currentSegmentStart, this.currentPosition);
        
        // 保存段落
        this.segments.push(segment);
        this.currentSegmentIndex++;
        
        // 更新段落起始位置
        this.currentSegmentStart = this.currentPosition;
        
        // 暂停输出
        this.isPaused = true;
        
        // 触发段落完成回调
        if (this.onSegmentComplete) {
            this.onSegmentComplete(segment, this.currentSegmentIndex);
        }
    }

    /**
     * 处理完成
     * @private
     */
    _handleComplete() {
        // 标记完成
        this.isComplete = true;
        
        // 清除定时器
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }
        
        // 触发完成回调
        if (this.onResponseComplete) {
            this.onResponseComplete(null, this.segments);
        }
    }

    /**
     * 继续输出
     * @param {Function} beforeContinue - 继续输出前执行的回调函数
     * @param {number} delay - 延迟时间（毫秒）
     */
    continue(beforeContinue = null, delay = 0) {
        // 如果提供了回调函数，先执行它
        if (beforeContinue && typeof beforeContinue === 'function') {
            beforeContinue();
        }

        // 添加延迟
        setTimeout(() => {
            // 取消暂停状态
            this.isPaused = false;
            
            // 继续打字
            this._startTyping();
        }, delay);
    }

    /**
     * 跳过当前段落
     * @param {Function} beforeSkip - 跳过前执行的回调函数
     */
    skip(beforeSkip = null) {
        // 如果提供了回调函数，先执行它
        if (beforeSkip && typeof beforeSkip === 'function') {
            beforeSkip();
        }

        // 找到下一个分段点
        let nextSegmentPos = this.fullResponse.length;
        
        // 查找下一个分隔符
        for (const delimiter of this.config.paragraphDelimiters) {
            const pos = this.fullResponse.indexOf(delimiter, this.currentPosition);
            if (pos !== -1 && pos < nextSegmentPos) {
                nextSegmentPos = pos + delimiter.length;
            }
        }
        
        // 如果没有找到分隔符，或者超过最大段落长度，使用最大段落长度
        const maxPos = this.currentSegmentStart + this.config.maxParagraphLength;
        if (maxPos < nextSegmentPos) {
            nextSegmentPos = maxPos;
        }
        
        // 更新当前位置
        this.currentPosition = nextSegmentPos;
        
        // 更新显示内容
        if (this.onContentUpdate) {
            this.onContentUpdate(this.fullResponse.substring(0, this.currentPosition));
        }
        
        // 完成当前段落
        this._completeCurrentSegment();
    }

    /**
     * 停止接收和处理
     */
    stop() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
            this.typingTimer = null;
        }

        // 标记完成
        this.isComplete = true;
        
        // 触发完成回调
        if (this.onResponseComplete) {
            this.onResponseComplete(null, this.segments);
        }
    }
}

// 导出StreamHandler类，使其可以被其他模块导入
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StreamHandler;
}