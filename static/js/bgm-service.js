/**
 * BGM Service (Web Audio 版)
 * 支持与其它 <audio>/<video> 同时播放
 * 支持每个页面独立的BGM配置
 */
class BGMService {
    constructor() {
        // 如果已存在实例，返回该实例
        if (window.bgmServiceInstance) {
            return window.bgmServiceInstance;
        }
        
        this.ctx = null;
        this.source = null;
        this.gainNode = null;
        this.buffer = null;
        this.isPlaying = false;
        this.volume = 0.5;
        this.bgmFolder = '/static/bgm/';
        this.currentTrack = null;
        this.tracks = [];
        this.enabled = true;
        this.pageConfigs = {};
        this.currentPage = null;
        
        // 新增：防重复播放机制
        this.lastPlayTime = 0;
        this.playCooldown = 2000; // 2秒冷却时间
        
        // 存储单例实例
        window.bgmServiceInstance = this;
        
        this.init();
    }

    async init() {
        // 1. 创建或复用 AudioContext
        if (!window.bgmAudioContext) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
            window.bgmAudioContext = this.ctx;
        } else {
            this.ctx = window.bgmAudioContext;
        }
        
        // 2. 加载歌单
        await this.loadTracks();
        
        // 3. 从localStorage加载设置
        const savedVolume = localStorage.getItem('bgmVolume');
        const bgmEnabled = localStorage.getItem('bgmEnabled') !== 'false';
        const savedPageConfigs = localStorage.getItem('pageBgmConfigs');
        
        if (savedVolume) {
            this.volume = parseFloat(savedVolume) / 100;
        }
        this.enabled = bgmEnabled;
        
        if (savedPageConfigs) {
            try {
                this.pageConfigs = JSON.parse(savedPageConfigs);
            } catch (e) {
                console.warn('Failed to parse page BGM configs:', e);
                this.pageConfigs = {};
            }
        }
        
        // 设置默认页面配置
        this.setDefaultPageConfigs();
        
        console.log('BGM Service (Web Audio) ready:', this.tracks);
        
        // 4. 如果启用BGM，尝试自动播放（根据当前页面配置）
        if (this.enabled && this.tracks.length) {
            // 如果当前页面已设置，播放页面BGM，否则播放随机
            if (this.currentPage) {
                this.playPageBGM();
            } else {
                this.playRandom();
            }
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

    setDefaultPageConfigs() {
        const pages = ['index', 'chat', 'story', 'story_chat', 'custom_character', 'select_character', 'settings'];
        pages.forEach(page => {
            if (!this.pageConfigs[page]) {
                this.pageConfigs[page] = {
                    track: 'random', // 'random', 'off', or specific track
                    enabled: true
                };
            }
        });
    }

    setCurrentPage(page) {
        // 如果页面没有变化，不需要重新播放
        if (this.currentPage === page) return;
        
        this.currentPage = page;
        this.playPageBGM();
    }

    async playPageBGM() {
        if (!this.currentPage || !this.enabled) return;
        
        const config = this.pageConfigs[this.currentPage];
        if (!config || !config.enabled || config.track === 'off') {
            this.stop();
            return;
        }
        
        if (config.track === 'random') {
            await this.playRandom();
        } else {
            await this.playTrack(config.track);
        }
    }

    getPageConfig(page) {
        return this.pageConfigs[page] || { track: 'random', enabled: true };
    }

    setPageConfig(page, config) {
        this.pageConfigs[page] = config;
        localStorage.setItem('pageBgmConfigs', JSON.stringify(this.pageConfigs));
        
        // 如果当前页面就是设置的页面，立即应用更改
        if (page === this.currentPage) {
            this.playPageBGM();
        }
    }

    getAvailablePages() {
        return ['index', 'chat', 'story', 'story_chat', 'custom_character', 'select_character', 'settings','about'];
    }

    getPageDisplayName(page) {
        const names = {
            'index': '主页',
            'chat': '聊天页面',
            'story': '故事页面',
            'story_chat': '故事聊天',
            'custom_character': '自定义角色',
            'select_character': '选择角色',
            'settings': '设置页面',
            'about': '关于页面'
        };
        return names[page] || page;
    }

    async fetchAndDecode(trackName) {
        const url = `${this.bgmFolder}${trackName}`;
        const res = await fetch(url);
        const arrayBuf = await res.arrayBuffer();
        return await this.ctx.decodeAudioData(arrayBuf);
    }

    async playTrack(trackName) {
        if (!this.enabled) return;
        
        // 新增：防重复播放检查
        const now = Date.now();
        if (now - this.lastPlayTime < this.playCooldown) {
            console.log(`BGM播放冷却中，跳过: ${trackName}`);
            return;
        }
        
        // 确保停止当前播放
        this.stop();
        
        try {
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
            this.lastPlayTime = now; // 记录播放时间
            console.log(`Playing BGM: ${trackName}`);
        } catch (error) {
            console.error('播放BGM失败:', error);
        }
    }

    // 修改清理方法
    cleanup() {
        this.stop();
        // 不要关闭全局的 AudioContext，只需停止当前播放
        this.source = null;
        this.gainNode = null;
        this.buffer = null;
        this.isPlaying = false;
    }

    async playRandom() {
        if (!this.enabled || !this.tracks.length) return;
        const r = Math.floor(Math.random() * this.tracks.length);
        await this.playTrack(this.tracks[r]);
    }

    pause() {
        if (!this.ctx || this.ctx.state === 'suspended') return;
        this.ctx.suspend();
        this.isPlaying = false;
    }

    resume() {
        if (!this.enabled || !this.ctx) return;
        this.ctx.resume().then(() => {
            this.isPlaying = true;
        });
    }

    stop() {
        if (this.source) {
            try {
                this.source.stop();
            } catch (e) {
                console.warn('Error stopping source:', e);
            }
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

// 修改全局初始化代码
if (!window.bgmService) {
    // 确保只绑定一次事件监听器
    if (!window.bgmEventListenersBound) {
        window.bgmService = new BGMService();
        
        // 页面卸载时清理资源但不关闭全局 AudioContext
        window.addEventListener('beforeunload', () => {
            if (window.bgmService) {
                window.bgmService.cleanup();
            }
        });
        
        // 用户第一次交互后启动 AudioContext
        const unlock = () => {
            if (window.bgmService && window.bgmService.ctx) {
                window.bgmService.ctx.resume().then(() => {
                    if (!window.bgmService.isPlaying && 
                        window.bgmService.tracks.length && 
                        window.bgmService.enabled) {
                        window.bgmService.playRandom();
                    }
                });
                // 只移除一次事件监听器
                if (!window.bgmUnlocked) {
                    ['click', 'keydown', 'touchstart'].forEach(e => 
                        document.removeEventListener(e, unlock));
                    window.bgmUnlocked = true;
                }
            }
        };
        
        ['click', 'keydown', 'touchstart'].forEach(e => 
            document.addEventListener(e, unlock));
        
        window.bgmEventListenersBound = true;
    }
}