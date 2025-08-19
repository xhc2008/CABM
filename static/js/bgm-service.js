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
        // 2. 加载歌单
        await this.loadTracks();
        console.log('BGM Service (Web Audio) ready:', this.tracks);
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

    async playTrack(trackName) {
        if (this.source) this.source.stop();   // 停掉上一首
        this.buffer = await this.fetchAndDecode(trackName);
        this.source = this.ctx.createBufferSource();
        this.source.buffer = this.buffer;
        this.source.loop = true;

        this.gainNode = this.ctx.createGain();
        this.gainNode.gain.value = this.volume;

        this.source.connect(this.gainNode).connect(this.ctx.destination);
        this.source.start();
        this.isPlaying = true;
        this.currentTrack = trackName;
        console.log(`Playing BGM: ${trackName}`);
    }

    async playRandom() {
        if (!this.tracks.length) return;
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
        if (!window.bgmService.isPlaying && window.bgmService.tracks.length) {
            window.bgmService.playRandom();
        }
    });
    ['click', 'keydown', 'touchstart'].forEach(e => document.removeEventListener(e, unlock));
};
['click', 'keydown', 'touchstart'].forEach(e => document.addEventListener(e, unlock));