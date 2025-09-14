/**
 * 流式响应处理器
 * 参考 stream.py 的处理方式，在前端实现流式数据的分段和控制
 */

// 常量配置
const OUTPUT_DELAY = 30; // 每个字符的输出间隔（毫秒）
const END_MARKER = "<END>"; // 结束标记符号
const PAUSE_MARKERS = ['。', '！', '？', '!', '?', '.', '…', '♪', '...','~']; // 暂停输出的分隔符号
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
        this.lastCharWasPauseMarker = false; // 新增：标记上一个字符是否为暂停标记
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
        // 检查是否是角色切换标记
        const switchMarkerMatch = data.match(/^<SWITCH_CHARACTER:([^:]+):([^>]+)>$/);
        if (switchMarkerMatch) {
            // 这是角色切换标记，添加特殊标记到缓冲区
            this.buffer.push({
                type: 'SWITCH_CHARACTER',
                characterID: switchMarkerMatch[1],
                characterName: switchMarkerMatch[2]
            });
        } else {
            // 将数据逐字符添加到缓冲区
            for (const char of data) {
                this.buffer.push(char);
            }
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

        // 如果暂停，停止处理
        if (this.isPaused) {
            return;
        }

        // 预览下一个项目，但不立即取出
        const nextItem = this.buffer[0];

        // 如果下一个项目是角色切换标记，需要特殊处理
        if (typeof nextItem === 'object' && nextItem.type === 'SWITCH_CHARACTER') {
            console.log('StreamProcessor: 发现角色切换标记，等待暂停后执行:', nextItem.characterName);
            
            // 检查当前段落是否有内容需要暂停
            if (this.currentParagraph && this.lastCharWasPauseMarker) {
                // 有内容且上一个字符是暂停标记，触发暂停
                this.handlePause();
                return; // 暂停处理，等待用户继续
            } else {
                // 没有内容需要暂停，立即执行角色切换
                const item = this.buffer.shift(); // 现在才真正取出
                console.log('StreamProcessor: 立即执行角色切换:', item.characterName);
                // 设置当前说话角色ID
                window.currentSpeakingCharacterId = item.characterID;
                // 执行角色切换
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName);
                }
                // 继续处理下一个项目
                this.processingTimeout = setTimeout(() => {
                    this.processingTimeout = null;
                    this.processBuffer();
                }, 0); // 立即处理下一个项目
                return;
            }
        }

        // 正常处理：取出一个字符
        const item = this.buffer.shift();

        const char = item;

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

        // 检查是否需要分割：上一个字符是暂停标记，当前字符不是暂停标记
        if (this.lastCharWasPauseMarker && !PAUSE_MARKERS.includes(char)) {
            // 检查下一个字符是否是结束标记
            const nextChar = this.buffer.length > 0 ? this.buffer[0] : null;

            // 只有在下一个字符不是结束标记时才暂停
            if (nextChar !== END_MARKER) {
                this.handlePause();
                // 重置标记
                this.lastCharWasPauseMarker = false;
                // 将当前字符放回缓冲区开头，下次处理时再处理
                this.buffer.unshift(char);
                return;
            }
        }

        // 正常字符处理
        this.currentParagraph += char;

        // 调用字符回调
        if (this.onCharacterCallback) {
            this.onCharacterCallback(this.paragraphs.join('') + this.currentParagraph);
        }

        // 更新暂停标记状态
        this.lastCharWasPauseMarker = PAUSE_MARKERS.includes(char);

        // 继续处理下一个字符
        this.processingTimeout = setTimeout(() => {
            this.processingTimeout = null;
            this.processBuffer();
        }, OUTPUT_DELAY);
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
        console.log('StreamProcessor.continue() called, isPaused:', this.isPaused, 'buffer length:', this.buffer.length);
        
        if (this.isPaused) {
            this.isPaused = false;
            console.log('Unpaused, continuing processing...');

            // 检查是否有待处理的角色切换标记
            const nextItem = this.buffer[0];
            if (typeof nextItem === 'object' && nextItem.type === 'SWITCH_CHARACTER') {
                console.log('StreamProcessor: 继续时执行角色切换:', nextItem.characterName);
                const item = this.buffer.shift(); // 取出角色切换标记
                // 设置当前说话角色ID
                window.currentSpeakingCharacterId = item.characterID;
                // 执行角色切换
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName);
                }
            }

            // 继续处理缓冲区
            if (!this.processingTimeout) {
                this.processBuffer();
            } else {
                console.log('Processing timeout already exists, not calling processBuffer');
            }
        } else {
            console.log('Not paused, no action needed');
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
        this.lastCharWasPauseMarker = false; // 重置暂停标记状态
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