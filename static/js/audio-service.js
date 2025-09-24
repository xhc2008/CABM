// 音频服务模块
import { loadingIndicator, currentMessage, errorMessage, errorContainer } from './dom-elements.js';

// 音频缓存对象和首次播放标记
const audioCache = {};
let firstAudioPlay = true;
let audioEnabled = true; // 音频是否已被用户启用

// 当前播放的音频对象
window.currentAudio = null;

// 新的音频队列管理
const audioQueue = new Map(); // Map<sentenceId, sentenceObj>
const audioBlobCache = new Map(); // Map<sentenceId, audioBlob>
let streamProcessor = null; // 引用到当前的流处理器

// 显示加载指示器
function showLoading() {
    loadingIndicator.style.display = 'flex';
}

// 隐藏加载指示器
function hideLoading() {
    loadingIndicator.style.display = 'none';
}

// 显示错误信息
function showError(message) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
}

// 播放指定文本的音频
export async function playTextAudio(text, currentCharacter, autoPlay = true) {
    // 检查TTS开关
    if (!window.ttsEnabled) {
        console.log('TTS已关闭，跳过音频播放');
        if (!autoPlay) {
            showError('TTS功能已关闭');
        }
        return;
    }

    if (!text || !text.trim()) {
        if (!autoPlay) showError('无法朗读空内容');
        return;
    }

    const textToPlay = text.trim();

    // 如果是自动播放但用户还没有启用音频，尝试播放（浏览器可能会阻止）
    if (autoPlay && !audioEnabled) {
        console.log('尝试自动播放（可能被浏览器阻止）');
        // 不直接返回，而是尝试播放，让浏览器决定是否允许
    }

    // 停止当前正在播放的音频，防止多个音频同时播放
    stopCurrentAudio();

    // 判断缓存
    let audioBlob = audioCache[textToPlay];
    if (audioBlob) {
        console.log('[playTextAudio] 命中缓存:', textToPlay);
        try {
            const audio = new Audio();
            const url = URL.createObjectURL(audioBlob);
            audio.src = url;
            audio.volume = window.ttsVolume || 0.8; // 应用TTS音量设置
            audio.onended = () => { URL.revokeObjectURL(url); };
            audio.onerror = () => { 
                if (!autoPlay) showError('音频播放失败'); 
                URL.revokeObjectURL(url); 
            };
            window.currentAudio = audio;
            
            // 尝试播放
            await audio.play();
            
            // 如果是用户首次主动播放，标记音频已启用
            if (!autoPlay) {
                audioEnabled = true;
            }
            
        } catch (error) {
            console.error('播放音频失败:', error);
            if (!autoPlay) {
                showError(`播放失败: ${error.message}`);
            } else {
                console.log('自动播放被阻止，这是正常的浏览器行为');
            }
        }
        return;
    } else {
        console.log('[playTextAudio] 未命中缓存，重新合成:', textToPlay);
        if (!autoPlay) {
            showLoading(); // 只有用户主动播放时才显示加载
        }
    }

    // 首次播放需要等待和弹窗
    if (firstAudioPlay && !autoPlay) {
        firstAudioPlay = false;
        alert('首次合成可能需要较长时间，请耐心等待。');
    }

    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textToPlay,
                role: currentCharacter ? currentCharacter.id : 'AI助手',
                enabled: window.ttsEnabled !== false
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || '获取音频失败');
        }

        const blob = await response.blob();
        if (blob.size === 0) {
            throw new Error('收到的音频数据为空');
        }
        
        // 缓存音频
        audioCache[textToPlay] = blob;

        const audio = new Audio();
        const url = URL.createObjectURL(blob);
        audio.src = url;
        audio.volume = window.ttsVolume || 0.8; // 应用TTS音量设置
        audio.onended = () => { URL.revokeObjectURL(url); };
        audio.onerror = () => { 
            if (!autoPlay) showError('音频播放失败'); 
            URL.revokeObjectURL(url); 
        };
        window.currentAudio = audio;
        
        // 根据播放类型决定是否播放
        try {
            await audio.play();
            
            // 如果是用户首次主动播放，标记音频已启用
            if (!autoPlay) {
                audioEnabled = true;
            }
        } catch (error) {
            if (!autoPlay) {
                throw error; // 用户主动播放时抛出错误
            } else {
                console.log('自动播放被阻止，这是正常的浏览器行为');
            }
        }
    } catch (error) {
        console.error('播放音频失败:', error);
        if (!autoPlay) {
            showError(`播放失败: ${error.message}`);
        }
    } finally {
        if (!autoPlay) {
            hideLoading();
        }
    }
}

// 播放音频（使用当前消息内容）
export async function playAudio(currentCharacter, autoPlay = true) {
    // 检查TTS开关
    if (!window.ttsEnabled) {
        console.log('TTS已关闭，跳过音频播放');
        if (!autoPlay) {
            showError('TTS功能已关闭');
        }
        return;
    }

    const text = currentMessage.textContent.trim();
    if (!text) {
        if (!autoPlay) showError('无法朗读空内容');
        return;
    }

    // 如果是自动播放但用户还没有启用音频，尝试播放（浏览器可能会阻止）
    if (autoPlay && !audioEnabled) {
        console.log('尝试自动播放（可能被浏览器阻止）');
        // 不直接返回，而是尝试播放，让浏览器决定是否允许
    }

    // 停止当前正在播放的音频，防止多个音频同时播放
    stopCurrentAudio();

    // 判断缓存
    let audioBlob = audioCache[text];
    if (audioBlob) {
        console.log('[playAudio] 命中缓存:', text);
        try {
            const audio = new Audio();
            const url = URL.createObjectURL(audioBlob);
            audio.src = url;
            audio.volume = window.ttsVolume || 0.8; // 应用TTS音量设置
            audio.onended = () => { URL.revokeObjectURL(url); };
            audio.onerror = () => { 
                if (!autoPlay) showError('音频播放失败'); 
                URL.revokeObjectURL(url); 
            };
            window.currentAudio = audio;
            
            // 尝试播放
            const playResult = await audio.play();
            
            // 如果是用户首次主动播放，标记音频已启用
            if (!autoPlay) {
                audioEnabled = true;
            }
            
        } catch (error) {
            console.error('播放音频失败:', error);
            if (!autoPlay) {
                showError(`播放失败: ${error.message}`);
            } else {
                console.log('自动播放被阻止，这是正常的浏览器行为');
            }
        }
        return;
    } else {
        console.log('[playAudio] 未命中缓存，重新合成:', text);
        if (!autoPlay) {
            showLoading(); // 只有用户主动播放时才显示加载
        }
    }

    // 首次播放需要等待和弹窗
    if (firstAudioPlay && !autoPlay) {
        firstAudioPlay = false;
        alert('首次合成可能需要较长时间，请耐心等待。');
    }

    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                role: currentCharacter ? currentCharacter.id : 'AI助手',
                enabled: window.ttsEnabled !== false
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || '获取音频失败');
        }

        const blob = await response.blob();
        if (blob.size === 0) {
            throw new Error('收到的音频数据为空');
        }
        
        // 缓存音频
        audioCache[text] = blob;

        const audio = new Audio();
        const url = URL.createObjectURL(blob);
        audio.src = url;
        audio.volume = window.ttsVolume || 0.8; // 应用TTS音量设置
        audio.onended = () => { URL.revokeObjectURL(url); };
        audio.onerror = () => { 
            if (!autoPlay) showError('音频播放失败'); 
            URL.revokeObjectURL(url); 
        };
        window.currentAudio = audio;
        
        // 根据播放类型决定是否播放
        try {
            await audio.play();
            
            // 如果是用户首次主动播放，标记音频已启用
            if (!autoPlay) {
                audioEnabled = true;
            }
        } catch (error) {
            if (!autoPlay) {
                throw error; // 用户主动播放时抛出错误
            } else {
                console.log('自动播放被阻止，这是正常的浏览器行为');
            }
        }
    } catch (error) {
        console.error('播放音频失败:', error);
        if (!autoPlay) {
            showError(`播放失败: ${error.message}`);
        }
    } finally {
        if (!autoPlay) {
            hideLoading();
        }
    }
}

// 停止当前音频播放
export function stopCurrentAudio() {
    if (window.currentAudio && typeof window.currentAudio.pause === 'function') {
        window.currentAudio.pause();
        window.currentAudio.currentTime = 0;
        window.currentAudio = null;
    }
}

// 设置流处理器引用
export function setStreamProcessor(processor) {
    streamProcessor = processor;
}

// 新的音频管理系统
export function preloadAudioForSentence(sentenceObj) {
    // 检查TTS开关
    if (!window.ttsEnabled) {
        console.log('TTS已关闭，跳过音频预加载');
        return;
    }

    if (!sentenceObj || !sentenceObj.text || !sentenceObj.text.trim()) {
        return;
    }

    const textToProcess = sentenceObj.text.trim();
    const sentenceId = sentenceObj.id;
    
    // 将句子信息加入队列
    audioQueue.set(sentenceId, sentenceObj);

    console.log(`[AudioService] 开始预加载音频 #${sentenceId}:`, sentenceObj.characterId,textToProcess);

    // 开始预加载
    fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: textToProcess,
            role: sentenceObj.characterId,
            enabled: window.ttsEnabled !== false
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('TTS请求失败');
        }
        return response.blob();
    })
    .then(blob => {
        if (blob && blob.size > 0) {
            audioBlobCache.set(sentenceId, blob);
            console.log(`[AudioService] 音频预加载完成 #${sentenceId}`);
        }
    })
    .catch(error => {
        console.error(`预加载音频失败 #${sentenceId}:`, error);
    });
}

// 根据索引播放音频
export function playNextAudioByIndex(sentenceIndex, isStreamMode = false) {
    // 尝试获取流处理器引用，优先使用模块级别的，然后尝试全局的
    let processor = streamProcessor;
    if (!processor && window.globalStreamProcessor) {
        processor = window.globalStreamProcessor;
        console.log('[AudioService] 使用全局流处理器引用');
    }
    
    if (!processor) {
        console.error('[AudioService] 流处理器引用未设置');
        return;
    }

    const sentenceObj = processor.getSentenceByIndex(sentenceIndex);
    if (!sentenceObj) {
        console.log(`[AudioService] 索引 ${sentenceIndex} 处没有句子信息`);
        return;
    }

    const sentenceId = sentenceObj.id;
    const audioBlob = audioBlobCache.get(sentenceId);
    
    if (audioBlob) {
        console.log(`[AudioService] 播放音频 #${sentenceId} (索引: ${sentenceIndex})`);
        playAudioBlobById(sentenceId, audioBlob, isStreamMode, () => {
            // 播放完成后的回调
            processor.incrementPlayIndex();
            // 清理已播放的音频缓存
            audioBlobCache.delete(sentenceId);
            audioQueue.delete(sentenceId);
        });
    } else {
        console.log(`[AudioService] 音频 #${sentenceId} (索引: ${sentenceIndex}) 尚未准备好，等待中...`);
        // 设置重试机制，但有限制次数
        let retryCount = 0;
        const maxRetries = 50; // 最多重试5秒
        const retryInterval = setInterval(() => {
            retryCount++;
            const audioBlob = audioBlobCache.get(sentenceId);
            if (audioBlob) {
                clearInterval(retryInterval);
                console.log(`[AudioService] 重试成功，播放音频 #${sentenceId} (索引: ${sentenceIndex})`);
                playAudioBlobById(sentenceId, audioBlob, isStreamMode, () => {
                    // 播放完成后的回调
                    processor.incrementPlayIndex();
                    // 清理已播放的音频缓存
                    audioBlobCache.delete(sentenceId);
                    audioQueue.delete(sentenceId);
                });
            } else if (retryCount >= maxRetries) {
                clearInterval(retryInterval);
                console.log(`[AudioService] 音频 #${sentenceId} (索引: ${sentenceIndex}) 等待超时，跳过播放`);
                // 即使跳过播放，也要增加索引，避免卡住
                processor.incrementPlayIndex();
            }
        }, 100);
    }
}


async function playAudioBlobById(sentenceId, audioBlob, isStreamMode = false, onPlayComplete = null) {
    try {
        // 停止当前正在播放的音频
        stopCurrentAudio();

        const audio = new Audio();
        const url = URL.createObjectURL(audioBlob);
        audio.src = url;
        audio.volume = window.ttsVolume || 0.8;
        audio.onended = () => { 
            URL.revokeObjectURL(url);
            
            // 调用播放完成回调
            if (onPlayComplete) {
                onPlayComplete();
            }
            
        };
        audio.onerror = () => { 
            console.error(`音频播放失败 #${sentenceId}`);
            URL.revokeObjectURL(url);
            
            // 调用播放完成回调（即使失败也要调用，确保索引正确更新）
            if (onPlayComplete) {
                onPlayComplete();
            }
            
        };
        
        window.currentAudio = audio;
        await audio.play();
    } catch (error) {
        console.error(`播放音频失败 #${sentenceId}:`, error);
        
        // 调用播放完成回调（即使失败也要调用，确保索引正确更新）
        if (onPlayComplete) {
            onPlayComplete();
        }
        
    }
}

export function resetAudioQueue() {
    audioQueue.clear();
    audioBlobCache.clear();
    stopCurrentAudio();
    streamProcessor = null;
}



// 语音识别相关
let recognition;
let firstMic = 0;

export function toggleRecording(messageInput, micButton, showError) {
    console.log('🔴 toggleRecording 被调用！');
    if (firstMic === 0) {
        firstMic = 1;
        alert('请确保你访问的地址为本地地址或https协议地址，否则浏览器可能会阻止调用麦克风！！！');
    }
    
    let isRecording = micButton.classList.toggle('recording');
    
    if (isRecording) {
        if (!recognition) {
            const SpeechRecognition = window.SpeechRecognition || 
                                    window.webkitSpeechRecognition ||
                                    window.mozSpeechRecognition || 
                                    window.msSpeechRecognition;
            
            if (!SpeechRecognition) {
                console.error('当前浏览器不支持语音识别API');
                showError('您的浏览器不支持语音识别功能');
                micButton.classList.remove('recording');
                return;
            }

            recognition = new SpeechRecognition();
            recognition.lang = 'zh-CN';
            recognition.interimResults = false;
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript.trim();
                if (transcript) {
                    messageInput.value += transcript;
                    // 语音识别后更新字数统计
                    if (window.inputEnhancements && typeof window.inputEnhancements.updateCharCount === 'function') {
                        window.inputEnhancements.updateCharCount();
                    }
                }
            };
            
            recognition.onerror = (event) => {
                console.error('语音识别错误:', event.error);
                showError(`语音识别错误: ${event.error}`);
                micButton.classList.remove('recording');
            };
            
            recognition.onend = () => {
                if (micButton.classList.contains('recording')) {
                    micButton.classList.remove('recording');
                }
            };
        }
        
        try {
            recognition.start();
        } catch (e) {
            console.error('启动语音识别失败:', e);
            showError('无法启动语音识别');
            micButton.classList.remove('recording');
        }
    } else {
        if (recognition) {
            recognition.stop();
        }
    }
}
// 暴露新的音频管理函数到全局
window.preloadAudioForSentence = preloadAudioForSentence;
window.playNextAudioByIndex = playNextAudioByIndex;
window.setStreamProcessor = setStreamProcessor;
window.resetAudioQueue = resetAudioQueue;