/**
 * 流式响应处理器
 * 参考 stream.py 的处理方式，在前端实现流式数据的分段和控制
 */

// 常量配置
const OUTPUT_DELAY = 100; // 每个字符的输出间隔（毫秒）
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
        
        // 音频预加载和播放管理
        this.sentenceCounter = 0; // 句子编号计数器
        this.isFirstSentence = true; // 标记是否是段落的第一句
        this.pendingSentence = ''; // 当前正在构建的句子
        this.completedSentences = []; // 已完成的句子列表，包含ID和文本
        this.nextPlaySentenceIndex = 0; // 下一个要播放的句子索引
        
        // 多角色模式支持：当前说话角色ID
        this.currentSpeakingCharacterId = null; // 为空时使用单角色模式，不为空时使用多角色模式
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
        // 检查是否是角色切换标记（可选携带情绪编号）
        const switchMarkerMatch = data.match(/^<SWITCH_CHARACTER:([^:]+):([^:>]+)(?::([^>]+))?>$/);
        if (switchMarkerMatch) {
            // 这是角色切换标记，添加特殊标记到缓冲区
            this.buffer.push({
                type: 'SWITCH_CHARACTER',
                characterID: switchMarkerMatch[1],
                characterName: switchMarkerMatch[2],
                characterMood: switchMarkerMatch[3] !== undefined ? switchMarkerMatch[3] : null
            });
        } else {
            // 将数据逐字符添加到缓冲区，同时检查句子完整性
            for (const char of data) {
                this.buffer.push(char);
                this.pendingSentence += char;
                
                // 检查是否形成完整句子
                if (PAUSE_MARKERS.includes(char)) {
                    this.handleCompleteSentence();
                }
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
                // 设置当前说话角色ID（多角色模式）
                this.currentSpeakingCharacterId = item.characterID;
                // 执行角色切换
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName, item.characterMood);
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

            // // 处理剩余的待处理句子
            // if (this.pendingSentence.trim()) {
            //     this.handleCompleteSentence();
            // }

            // 段落结束，重置音频相关状态和当前说话角色
            this.isFirstSentence = true;
            this.currentSpeakingCharacterId = null; // 段落结束后重置当前角色

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

        // 不在第一个字符时就播放，等到句子检测完成后再播放

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

        // // 处理剩余的待处理句子
        // if (this.pendingSentence.trim()) {
        //     this.handleCompleteSentence();
        // }

        // 段落暂停后重置当前说话角色
        this.currentSpeakingCharacterId = null;

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
                // 设置当前说话角色ID（多角色模式）
                this.currentSpeakingCharacterId = item.characterID;
                // 执行角色切换
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName, item.characterMood);
                }
            }

            // 继续时播放音频（单次播放模式）
            if (window.playNextAudioByIndex) {
                console.log(`[StreamProcessor] 继续播放，当前索引: ${this.nextPlaySentenceIndex}`);
                window.playNextAudioByIndex(this.nextPlaySentenceIndex, false); // 单次播放模式
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
     * 处理完整句子 - 开始预加载音频
     */
    handleCompleteSentence() {
        if (!this.pendingSentence.trim()) {
            return;
        }
        
        const sentenceText = this.pendingSentence.trim();
        const sentenceId = ++this.sentenceCounter;
        
        // 创建句子对象，嵌入ID
        const sentenceObj = {
            id: sentenceId,
            text: sentenceText,
            characterId: null
        };
        // 多角色模式：如果设置了当前说话角色ID，使用它
        if (this.currentSpeakingCharacterId) {
            console.log("当前TTS角色：",this.currentSpeakingCharacterId)
            sentenceObj.characterId = this.currentSpeakingCharacterId;
        }
        else
        {
            // 获取当前角色信息
            const character = this.getCurrentCharacterInfo();
            if (character) {
                sentenceObj.characterId = character.id;
            }
        }
        
        // 添加到已完成句子列表
        this.completedSentences.push(sentenceObj);
        
        console.log(`[StreamProcessor] 检测到完整句子 #${sentenceId}:`, sentenceText);
        
        // 调用audio-service.js的预加载函数
        if (window.preloadAudioForSentence) {
            window.preloadAudioForSentence(sentenceObj);
        }
        
        // 检查是否是第一句话，如果是则开始播放
        if (this.isFirstSentence) {
            console.log('[StreamProcessor] 第一句话检测完成，开始流式播放音频');
            this.isFirstSentence = false;
            // 延迟一点时间确保预加载开始
            setTimeout(() => {
                if (window.playNextAudioByIndex) {
                    window.playNextAudioByIndex(0, false); // 流式模式，从索引0开始
                }
            }, 100);
        }
        
        // 清空待处理句子
        this.pendingSentence = '';
    }

    /**
     * 获取当前角色信息
     */
    getCurrentCharacterInfo() {
        // 单角色模式：使用原来的方法
        if (window.getCurrentCharacter) {
            return window.getCurrentCharacter();
        }
        return null;
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
        
        // 重置音频相关状态
        this.sentenceCounter = 0;
        this.isFirstSentence = true;
        this.pendingSentence = '';
        this.completedSentences = [];
        this.nextPlaySentenceIndex = 0;
        
        // 重置当前说话角色
        this.currentSpeakingCharacterId = null;
        
        // 调用audio-service.js的重置函数
        if (window.resetAudioQueue) {
            window.resetAudioQueue();
        }
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

    /**
     * 获取指定索引的句子信息
     */
    getSentenceByIndex(index) {
        return this.completedSentences[index] || null;
    }

    /**
     * 增加下一个播放句子的索引
     */
    incrementPlayIndex() {
        this.nextPlaySentenceIndex++;
        return this.nextPlaySentenceIndex;
    }

}

// 导出类
window.StreamProcessor = StreamProcessor;