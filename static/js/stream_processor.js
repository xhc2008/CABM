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
        this.buffer = []; // 现在存储句子对象而不是字符
        this.active = true;
        this.isPaused = false;
        this.currentParagraph = '';
        this.paragraphs = [];
        this.onCharacterCallback = null;
        this.onPauseCallback = null;
        this.onCompleteCallback = null;
        this.processingTimeout = null;
        
        // 音频预加载和播放管理
        this.completedSentences = []; // 已完成的句子列表，包含ID和文本
        this.currentPlayingSentenceId = 0; // 当前正在播放的句子ID
        this.isFirstSentence = true; // 标记是否是段落的第一句
        
        // 句子构建状态
        this.pendingSentence = ''; // 当前正在构建的句子（跨多次addData调用）
        
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
     * 添加数据到缓冲区 - 现在逐句添加
     */
    addData(data) {
        // 检查是否是角色切换标记（可选携带情绪编号）
        const switchMarkerMatch = data.match(/^<SWITCH_CHARACTER:([^:]+):([^:>]+)(?::([^>]+))?>$/);
        if (switchMarkerMatch) {
            this.currentSpeakingCharacterId = switchMarkerMatch[1];
            console.log(`[StreamProcessor] 在addData中更新当前说话角色: ${this.currentSpeakingCharacterId}`);
            
            // 这是角色切换标记，添加特殊标记到缓冲区
            this.buffer.push({
                type: 'SWITCH_CHARACTER',
                characterID: switchMarkerMatch[1],
                characterName: switchMarkerMatch[2],
                characterMood: switchMarkerMatch[3] !== undefined ? switchMarkerMatch[3] : null
            });
        } else {
            // 将数据按句子分割并添加到缓冲区
            this.splitIntoSentences(data);
        }

        // 如果没有在处理且没有暂停，开始处理
        if (!this.processingTimeout && this.active && !this.isPaused) {
            this.processBuffer();
        }
    }

    /**
     * 将数据分割成句子对象并添加到缓冲区
     */
    splitIntoSentences(data) {
        // 将新数据添加到待处理句子中
        this.pendingSentence += data;
        
        // 查找完整句子
        let lastCompleteIndex = -1;
        for (let i = 0; i < this.pendingSentence.length; i++) {
            if (PAUSE_MARKERS.includes(this.pendingSentence[i])) {
                lastCompleteIndex = i;
            }
        }
        
        // 如果找到完整句子
        if (lastCompleteIndex >= 0) {
            const completeSentenceText = this.pendingSentence.substring(0, lastCompleteIndex + 1);
            const remainingText = this.pendingSentence.substring(lastCompleteIndex + 1);
            
            if (completeSentenceText.trim()) {
                const sentenceId = this.completedSentences.length + 1;
                
                // 创建句子对象，嵌入ID
                const sentenceObj = {
                    id: sentenceId,
                    text: completeSentenceText.trim(),
                    characterId: null,
                    type: 'SENTENCE'
                };
                
                // 多角色模式：如果设置了当前说话角色ID，使用它
                if (this.currentSpeakingCharacterId) {
                    sentenceObj.characterId = this.currentSpeakingCharacterId;
                } else {
                    // 获取当前角色信息
                    const character = this.getCurrentCharacterInfo();
                    if (character) {
                        sentenceObj.characterId = character.id;
                    }
                }
                
                // 添加到缓冲区和已完成句子列表
                this.buffer.push(sentenceObj);
                this.completedSentences.push(sentenceObj);
                
                console.log(`[StreamProcessor] 创建句子对象 #${sentenceObj.id}:`, sentenceObj.text);
                
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
                        if (window.playNextAudioBySentenceId) {
                            window.playNextAudioBySentenceId(sentenceId); // 使用句子ID
                        }
                    }, 100);
                }
            }
            
            // 更新待处理句子为剩余部分
            this.pendingSentence = remainingText;
        }
    }

    /**
     * 标记数据结束
     */
    markEnd() {
        this.buffer.push({ type: 'END_MARKER' });
        this.active = false;

        // 如果没有在处理，开始处理
        if (!this.processingTimeout) {
            this.processBuffer();
        }
    }

    /**
     * 处理缓冲区数据 - 现在处理句子对象
     */
    processBuffer() {
        if (this.buffer.length === 0 || this.processingTimeout) {
            return;
        }

        // 如果暂停，停止处理
        if (this.isPaused) {
            return;
        }

        // 取出下一个项目
        const item = this.buffer.shift();

        // 如果是角色切换标记
        if (item.type === 'SWITCH_CHARACTER') {
            console.log('StreamProcessor: 发现角色切换标记，等待暂停后执行:', item.characterName);
            
            // 检查当前段落是否有内容需要暂停
            if (this.currentParagraph) {
                // 有内容，触发暂停
                this.handlePause();
                // 将角色切换标记放回缓冲区开头，暂停后再处理
                this.buffer.unshift(item);
                return;
            } else {
                // 没有内容需要暂停，立即执行角色切换
                console.log('StreamProcessor: 立即执行角色切换:', item.characterName);
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName, item.characterMood);
                }
                // 继续处理下一个项目
                this.processingTimeout = setTimeout(() => {
                    this.processingTimeout = null;
                    this.processBuffer();
                }, 0);
                return;
            }
        }

        // 如果是结束标记
        if (item.type === 'END_MARKER') {
            // 如果还有未处理的段落，添加到结果中
            if (this.currentParagraph) {
                this.paragraphs.push(this.currentParagraph);
                this.currentParagraph = '';
            }

            // 段落结束，重置音频相关状态和当前说话角色
            this.isFirstSentence = true;
            this.currentSpeakingCharacterId = null;

            // 调用完成回调
            if (this.onCompleteCallback) {
                this.onCompleteCallback(this.paragraphs.join(''));
            }
            return;
        }

        // 处理句子对象
        if (item.type === 'SENTENCE') {
            console.log(`[StreamProcessor] 开始逐字输出句子 #${item.id}:`, item.text);
            
            // 在开始输出句子时播放音频
            if (window.playNextAudioBySentenceId) {
                console.log(`[StreamProcessor] 开始播放句子音频 #${item.id}`);
                window.playNextAudioBySentenceId(item.id);
            }
            
            this.outputSentenceCharByChar(item.text);
            return;
        }
    }

    /**
     * 逐字输出句子内容
     */
    outputSentenceCharByChar(sentenceText) {
        let charIndex = 0;
        
        const outputNextChar = () => {
            if (charIndex < sentenceText.length && !this.isPaused) {
                const char = sentenceText[charIndex];
                this.currentParagraph += char;
                charIndex++;
                
                // 调用字符回调
                if (this.onCharacterCallback) {
                    this.onCharacterCallback(this.paragraphs.join('') + this.currentParagraph);
                }
                
                // 继续输出下一个字符
                this.processingTimeout = setTimeout(() => {
                    this.processingTimeout = null;
                    outputNextChar();
                }, OUTPUT_DELAY);
            } else if (charIndex >= sentenceText.length) {
                // 句子输出完成，触发暂停（因为一句输出完了就是暂停）
                this.handlePause();
            }
            // 如果isPaused为true，则停止输出，等待continue()调用
        };
        
        outputNextChar();
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
            if (nextItem && nextItem.type === 'SWITCH_CHARACTER') {
                console.log('StreamProcessor: 继续时执行角色切换:', nextItem.characterName);
                const item = this.buffer.shift(); // 取出角色切换标记
                // 执行角色切换
                if (window.switchToCharacter) {
                    window.switchToCharacter(item.characterID, item.characterName, item.characterMood);
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

        // 将所有缓冲区中的句子内容添加到当前段落
        let remainingContent = '';
        while (this.buffer.length > 0) {
            const item = this.buffer.shift();
            if (item.type === 'END_MARKER') {
                break;
            }
            if (item.type === 'SENTENCE') {
                remainingContent += item.text;
            }
            // 跳过角色切换标记
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
        
        // 重置句子构建状态
        this.pendingSentence = '';
        
        // 重置音频相关状态
        this.isFirstSentence = true;
        this.completedSentences = [];
        this.currentPlayingSentenceId = 0;
        
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
     * 根据句子ID获取句子信息
     */
    getSentenceBySentenceId(sentenceId) {
        return this.completedSentences.find(sentence => sentence.id === sentenceId) || null;
    }

    /**
     * 更新当前播放的句子ID
     */
    setCurrentPlayingSentenceId(sentenceId) {
        this.currentPlayingSentenceId = sentenceId;
        return this.currentPlayingSentenceId;
    }

    /**
     * 获取下一个未播放的句子
     */
    getNextUnplayedSentence() {
        // 查找ID大于当前播放ID的第一个句子
        return this.completedSentences.find(sentence => sentence.id > this.currentPlayingSentenceId) || null;
    }

}

// 导出类
window.StreamProcessor = StreamProcessor;