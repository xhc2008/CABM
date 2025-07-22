/**
 * 流式响应处理器
 * 负责处理AI的流式响应，实现分段显示和用户控制
 */
class StreamHandler {
    constructor(config) {
        // 配置
        this.config = {
            paragraphDelimiters: ["。", "！", "？", ".", "!", "?"], // 段落分隔符
            endToken: "[DONE]",                                   // 结束标记
            ...config
        };

        // 队列和状态
        this.inputQueue = [];        // 接收队列
        this.outputQueue = [];       // 输出队列
        this.currentParagraph = "";  // 当前段落
        this.paragraphs = [];        // 已完成段落
        this.fullResponse = "";      // 完整响应

        // 状态标志
        this.isReceiving = false;    // 是否正在接收数据
        this.isPaused = false;       // 是否暂停输出
        this.isComplete = false;     // 是否接收完成
        this.currentSegmentIndex = 0;// 当前段落索引

        // 回调函数
        this.onSegmentComplete = null;   // 段落完成回调
        this.onResponseComplete = null;  // 响应完成回调
        this.onContentUpdate = null;     // 内容更新回调
    }

    /**
     * 重置状态
     */
    reset() {
        this.inputQueue = [];
        this.outputQueue = [];
        this.currentParagraph = "";
        this.paragraphs = [];
        this.fullResponse = "";
        this.isReceiving = false;
        this.isPaused = false;
        this.isComplete = false;
        this.currentSegmentIndex = 0;
    }

    /**
     * 开始接收流式响应
     * @param {ReadableStream} stream - 响应流
     */
    async startReceiving(stream) {
        if (this.isReceiving) {
            console.warn("已经在接收流式响应");
            return;
        }

        // 重置状态
        this.reset();
        this.isReceiving = true;

        // 创建读取器和解码器
        const reader = stream.getReader();
        const decoder = new TextDecoder();

        // 启动输出处理
        this._startOutputProcessing();

        try {
            // 读取流式响应
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                // 解码响应数据
                const chunk = decoder.decode(value, { stream: true });

                // 处理数据块
                this._processChunk(chunk);
            }
        } catch (error) {
            console.error("读取流式响应失败:", error);
            // 确保结束标记被添加到队列
            this.inputQueue.push({ type: "end" });
        }
    }

    /**
     * 处理数据块
     * @param {string} chunk - 数据块
     */
    _processChunk(chunk) {
        // 分割行
        const lines = chunk.split('\n').filter(line => line.trim());

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const jsonStr = line.slice(6);

                // 检查是否是结束标记
                if (jsonStr === this.config.endToken) {
                    this.inputQueue.push({ type: "end" });
                    this.isComplete = true;
                    continue;
                }

                try {
                    const data = JSON.parse(jsonStr);

                    // 处理流式控制信息
                    if (data.stream_control) {
                        // 如果段落完成且需要暂停
                        if (data.stream_control.paragraph_complete && data.stream_control.pause) {
                            // 添加段落到队列
                            if (data.stream_control.paragraph) {
                                this.inputQueue.push({
                                    type: "paragraph",
                                    content: data.stream_control.paragraph
                                });
                            }
                            continue;
                        }

                        // 如果是结束标记
                        if (data.stream_control.is_complete) {
                            this.isComplete = true;
                            this.inputQueue.push({ type: "end" });
                            continue;
                        }

                        // 处理增量内容
                        if (data.stream_control.content) {
                            this.inputQueue.push({
                                type: "content",
                                content: data.stream_control.content
                            });
                        }
                    }
                    // 处理标准格式
                    else if (data.choices && data.choices[0] && data.choices[0].delta) {
                        const delta = data.choices[0].delta;

                        if (delta.content) {
                            // 将内容拆分为单个字符，以实现更流畅的字符输出
                            const content = delta.content;
                            for (let i = 0; i < content.length; i++) {
                                this.inputQueue.push({
                                    type: "content",
                                    content: content.charAt(i)
                                });
                            }
                        }
                    }
                    // 直接处理内容字段
                    else if (data.content) {
                        // 将内容拆分为单个字符，以实现更流畅的字符输出
                        const content = data.content;
                        for (let i = 0; i < content.length; i++) {
                            this.inputQueue.push({
                                type: "content",
                                content: content.charAt(i)
                            });
                        }
                    }
                } catch (e) {
                    console.error('解析JSON失败:', e, jsonStr);
                }
            }
        }
    }

    /**
     * 启动输出处理
     */
    async _startOutputProcessing() {
        // 创建一个异步函数来处理输出队列
        const processOutput = async () => {
            // 添加初始延迟，确保输出稳定性
            await new Promise(resolve => setTimeout(resolve, 300));

            // 标记是否是新段落开始
            let isNewSegment = true;

            while (true) {
                // 如果暂停输出，等待
                if (this.isPaused) {
                    await new Promise(resolve => setTimeout(resolve, 100));
                    continue;
                }

                // 如果输出队列为空
                if (this.outputQueue.length === 0) {
                    // 如果输入队列也为空且未完成，等待
                    if (this.inputQueue.length === 0 && !this.isComplete) {
                        await new Promise(resolve => setTimeout(resolve, 50));
                        continue;
                    }

                    // 从输入队列移动项目到输出队列
                    while (this.inputQueue.length > 0) {
                        const item = this.inputQueue.shift();
                        this.outputQueue.push(item);

                        // 如果是段落或结束标记，只移动一个
                        if (item.type === "paragraph" || item.type === "end") {
                            break;
                        }
                    }

                    // 如果输出队列仍为空且已完成，退出循环
                    if (this.outputQueue.length === 0 && this.isComplete) {
                        break;
                    }

                    // 如果输出队列仍为空，等待
                    if (this.outputQueue.length === 0) {
                        await new Promise(resolve => setTimeout(resolve, 50));
                        continue;
                    }

                    // 如果是新段落开始，添加延迟
                    if (isNewSegment) {
                        await new Promise(resolve => setTimeout(resolve, 300));
                        isNewSegment = false;
                    }
                }

                // 处理输出队列中的项目
                const item = this.outputQueue.shift();

                switch (item.type) {
                    case "content":
                        // 添加内容到当前段落
                        this.currentParagraph += item.content;

                        // 只有在非暂停状态下才更新fullResponse
                        if (!this.isPaused) {
                            this.fullResponse += item.content;
                        }

                        // 检查是否有完整段落
                        let foundDelimiter = false;
                        let delimiterIndex = -1;
                        let foundDelimiterChar = '';

                        // 查找第一个出现的分隔符
                        for (const delimiter of this.config.paragraphDelimiters) {
                            const index = this.currentParagraph.indexOf(delimiter);
                            if (index !== -1 && (delimiterIndex === -1 || index < delimiterIndex)) {
                                delimiterIndex = index;
                                foundDelimiterChar = delimiter;
                                foundDelimiter = true;
                            }
                        }

                        // 如果找到分隔符
                        if (foundDelimiter) {
                            // 分割段落：前面部分 + 分隔符
                            const completeParagraph = this.currentParagraph.substring(0, delimiterIndex + 1);
                            // 剩余部分
                            const remainingPart = this.currentParagraph.substring(delimiterIndex + 1);

                            // 添加完整段落到结果
                            this.paragraphs.push(completeParagraph);

                            // 调用段落完成回调
                            if (this.onSegmentComplete) {
                                this.currentSegmentIndex++;
                                this.isPaused = true;
                                this.onSegmentComplete(completeParagraph, this.currentSegmentIndex);
                            }

                            // 如果暂停了，保存剩余部分到缓冲区
                            if (this.isPaused) {
                                this.buffer = remainingPart + this.buffer;
                                break;
                            }

                            // 如果没有暂停，更新当前段落为剩余部分
                            this.currentParagraph = remainingPart;

                            // 标记为新段落开始
                            isNewSegment = true;
                        }

                        // 调用内容更新回调
                        if (this.onContentUpdate && !this.isPaused) {
                            this.onContentUpdate(this.fullResponse);
                            // 添加字符输出延迟 - 减少延迟以实现更流畅的字符输出
                            await new Promise(resolve => setTimeout(resolve, 1));
                        }
                        break;

                    case "paragraph":
                        // 添加完整段落
                        this.paragraphs.push(item.content);
                        this.fullResponse += item.content;
                        this.currentParagraph = "";

                        // 调用段落完成回调
                        if (this.onSegmentComplete) {
                            this.currentSegmentIndex++;
                            this.isPaused = true;
                            this.onSegmentComplete(item.content, this.currentSegmentIndex);
                        }

                        // 调用内容更新回调
                        if (this.onContentUpdate && !this.isPaused) {
                            this.onContentUpdate(this.fullResponse);
                            // 添加字符输出延迟 - 减少延迟以实现更流畅的字符输出
                            await new Promise(resolve => setTimeout(resolve, 1));
                        }
                        break;

                    case "end":
                        // 如果还有未处理的段落或缓冲区，添加到结果中
                        const finalContent = this.buffer + this.currentParagraph;
                        if (finalContent && finalContent.trim()) {
                            this.paragraphs.push(finalContent);
                            this.fullResponse += finalContent;

                            // 调用段落完成回调
                            if (this.onSegmentComplete) {
                                this.currentSegmentIndex++;
                                // 传递最终内容
                                this.onSegmentComplete(finalContent, this.currentSegmentIndex);
                            }

                            // 清空缓冲区和当前段落
                            this.buffer = "";
                            this.currentParagraph = "";
                        }

                        console.log("输出完成，最终段落:", finalContent);

                        // 调用响应完成回调
                        if (this.onResponseComplete) {
                            this.onResponseComplete(this.fullResponse, this.paragraphs);
                        }

                        // 标记为完成
                        this.isComplete = true;
                        break;
                }

                // 如果暂停了，等待用户点击继续
                if (this.isPaused) {
                    continue;
                }

                // 短暂等待，避免过度占用CPU
                await new Promise(resolve => setTimeout(resolve, 1));
            }
        };

        // 启动处理
        processOutput();
    }

    /**
     * 继续输出
     */
    continue() {
        // 清空当前显示的内容，以便开始新段落
        this.fullResponse = "";
        this.isPaused = false;

        // 通知内容已清空，准备显示新段落
        if (this.onContentUpdate) {
            this.onContentUpdate("");
        }

        // 如果缓冲区中有内容，将其移动到当前段落
        if (this.buffer) {
            this.currentParagraph = this.buffer + this.currentParagraph;
            this.buffer = "";

            // 立即更新显示
            if (this.onContentUpdate) {
                this.onContentUpdate(this.currentParagraph);
            }
        }

        console.log("继续输出，当前段落:", this.currentParagraph);
    }

    /**
     * 暂停输出
     */
    pause() {
        this.isPaused = true;
    }

    /**
     * 跳过当前段落
     */
    skip() {
        this.isPaused = false;
    }

    /**
     * 获取完整响应
     */
    getFullResponse() {
        return this.fullResponse;
    }

    /**
     * 获取所有段落
     */
    getParagraphs() {
        return [...this.paragraphs];
    }
}

// 导出
window.StreamHandler = StreamHandler;