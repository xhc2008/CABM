/**
 * BGM Service (Web Audio 版)
 * 支持与其它 <audio>/<video> 同时播放
 */
class BGMService {
    constructor() {
        this.ctx = null;          // AudioContext
        this.source = null;       // AudioBufferSourceNode
        this.gainNode = null;     // GainNode（音量）
        this.buffer = null;       // 解码后的音频数据
        this.isPlaying = false;
        this.volume = 0.5;
        this.bgmFolder = '/static/bgm/';
        this.currentTrack = null;
        this.tracks = [];
        this.init();
    }

    async init() {
        // 1. 创建 AudioContext（需要在用户手势后 resume）
        this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        // 2. 加载歌单和设置
        await this.loadTracks();
        await this.loadSettings();
        console.log('BGM Service (Web Audio) ready:', this.tracks);
        // 3. 根据设置决定是否自动播放
        if (this.tracks.length && this.bgmEnabled) {
            this.playRandom();
        }
    }

    async loadSettings() {
        try {
            const res = await fetch('/api/settings');
            if (res.ok) {
                const settings = await res.json();
                this.bgmEnabled = settings.audio?.bgm_enabled !== false; // 默认启用
                this.volume = settings.audio?.bgm_volume || 0.5;
                console.log('BGM Settings loaded:', { enabled: this.bgmEnabled, volume: this.volume });
            } else {
                this.bgmEnabled = true; // 默认启用
            }
        } catch (error) {
            console.error('Failed to load BGM settings:', error);
            this.bgmEnabled = true; // 默认启用
        }
    }

    async loadTracks() {
        try {
            const res = await fetch('/api/bgm-tracks');
            this.tracks = res.ok ? await res.json() : ['bgm01.aac'];
        } catch {
            this.tracks = ['bgm01.aac'];
        }
    }

    async fetchAndDecode(trackName) {
        const url = `${this.bgmFolder}${trackName}`;
        const res = await fetch(url);
        const arrayBuf = await res.arrayBuffer();
        return await this.ctx.decodeAudioData(arrayBuf);
    }

    async playTrack(trackName, startTime = 0) {
        if (this.source) this.source.stop();   // 停掉上一首
        this.buffer = await this.fetchAndDecode(trackName);
        this.source = this.ctx.createBufferSource();
        this.source.buffer = this.buffer;
        this.source.loop = false; // 不循环，才能触发 ended
        // 播放完自动随机下一首
        this.source.onended = () => {
            this.isPlaying = false;
            this.playRandom();
        };

        this.gainNode = this.ctx.createGain();
        this.gainNode.gain.value = this.volume;

        this.source.connect(this.gainNode).connect(this.ctx.destination);
        this.source.start(0, startTime);
        this.isPlaying = true;
        this.currentTrack = trackName;
        this._startProgressSaver();
        console.log(`Playing BGM: ${trackName} from ${startTime}s`);
    }

    _startProgressSaver() {
        if (this._progressTimer) clearInterval(this._progressTimer);
        this._progressTimer = setInterval(() => {
            if (this.isPlaying && this.ctx && this.ctx.state === 'running' && this.source) {
                const currentTime = this.ctx.currentTime;
                localStorage.setItem('bgm_progress', JSON.stringify({
                    track: this.currentTrack,
                    time: currentTime % this.buffer.duration
                }));
            }
        }, 500);
    }

    _stopProgressSaver() {
        if (this._progressTimer) clearInterval(this._progressTimer);
        this._progressTimer = null;
    }

    async playRandom() {
        if (!this.tracks.length) return;
        // 检查本地是否有保存进度
        const saved = localStorage.getItem('bgm_progress');
        if (saved) {
            try {
                const { track, time } = JSON.parse(saved);
                if (this.tracks.includes(track)) {
                    await this.playTrack(track, time || 0);
                    return;
                }
            } catch {}
        }
        const r = Math.floor(Math.random() * this.tracks.length);
        await this.playTrack(this.tracks[r]);
    }

    pause() {
        if (!this.ctx || this.ctx.state === 'suspended') return;
        this.ctx.suspend();
        this.isPlaying = false;
    }

    resume() {
        if (!this.ctx) return;
        this.ctx.resume().then(() => {
            this.isPlaying = true;
        });
    }

    stop() {
        if (this.source) {
            this.source.stop();
            this.source = null;
            this.isPlaying = false;
            this._stopProgressSaver();
        }
    }

    toggle() {
        if (this.isPlaying) this.pause();
        else this.currentTrack ? this.resume() : this.playRandom();
        return this.isPlaying;
    }

    setVolume(v) {
        this.volume = Math.max(0, Math.min(1, v));
        if (this.gainNode) this.gainNode.gain.value = this.volume;
    }

    getVolume() { return this.volume; }
    getPlayingState() { return this.isPlaying; }
    getCurrentTrack() { return this.currentTrack; }
    getAvailableTracks() { return [...this.tracks]; }
    async refreshTracks() { await this.loadTracks(); }
}

// 全局实例
window.bgmService = new BGMService();

// 用户第一次交互后启动 AudioContext
const unlock = () => {
    window.bgmService.ctx.resume().then(() => {
        if (!window.bgmService.isPlaying && window.bgmService.tracks.length && window.bgmService.bgmEnabled) {
            window.bgmService.playRandom();
        }
    });
    ['click', 'keydown', 'touchstart'].forEach(e => document.removeEventListener(e, unlock));
};
['click', 'keydown', 'touchstart'].forEach(e => document.addEventListener(e, unlock));
