// 音频服务模块
import { loadingIndicator, currentMessage, errorMessage, errorContainer } from './dom-elements.js';

// 音频缓存对象和首次播放标记
const audioCache = {};
let firstAudioPlay = true;
let audioEnabled = true; // 音频是否已被用户启用

// 当前播放的音频对象
window.currentAudio = null;

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

// 播放音频
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

    // 如果是自动播放但用户还没有启用音频，就不播放
    if (autoPlay && !audioEnabled) {
        console.log('自动播放跳过：用户尚未启用音频');
        return;
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
                role: currentCharacter ? currentCharacter.name : 'AI助手'
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

// 预加载音频
export function prefetchAudio(text, roleName, callback) {
    // 检查TTS开关
    if (!window.ttsEnabled) {
        console.log('TTS已关闭，跳过音频预加载');
        if (callback) callback();
        return;
    }

    if (!text) {
        if (callback) callback();
        return;
    }
    
    if (audioCache[text]) {
        // 命中缓存时，直接同步调用回调，避免异步等待
        if (callback) callback();
        return;
    }
    
    fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: text,
            role: roleName || 'AI助手'
        })
    })
    .then(response => {
        if (!response.ok) return Promise.reject();
        return response.blob();
    })
    .then(blob => {
        if (blob && blob.size > 0) {
            audioCache[text] = blob;
        }
        if (callback) callback();
    })
    .catch(() => {
        if (callback) callback();
    });
}

// 停止当前音频播放
export function stopCurrentAudio() {
    if (window.currentAudio && typeof window.currentAudio.pause === 'function') {
        window.currentAudio.pause();
        window.currentAudio.currentTime = 0;
        window.currentAudio = null;
    }
}

// 语音识别相关
let recognition;
let firstMic = 0;

export function toggleRecording(messageInput, micButton, showError) {
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
