/**
 * BGM Service (Web Audio 版) - 改进版
 * 解决重复播放问题
 */
class BGMService {
    constructor() {
        // 强制单例模式
        if (window.bgmServiceInstance) {
            console.log('BGM Service: 返回现有实例');
            return window.bgmServiceInstance;
        }

        // 防止并发创建
        if (window.bgmServiceCreating) {
            console.warn('BGM Service: 正在创建中，等待完成');
            return new Promise(resolve => {
                const checkInterval = setInterval(() => {
                    if (window.bgmServiceInstance) {
                        clearInterval(checkInterval);
                        resolve(window.bgmServiceInstance);
                    }
                }, 50);
            });
        }

        window.bgmServiceCreating = true;

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

        // 防重复播放机制
        this.lastPlayTime = 0;
        this.playCooldown = 2000; // 2秒冷却时间
        this.playingPromise = null; // 跟踪播放状态
        this.lastRandomTrack = null; // 记录上一首随机播放的歌曲

        // 存储单例实例
        window.bgmServiceInstance = this;
        window.bgmServiceCreating = false;

        console.log('BGM Service: 创建新实例');
        this.init();
    }

    async init() {
        console.log('BGM Service: 开始初始化');

        // 1. 创建或复用 AudioContext
        if (!window.sharedBGMAudioContext) {
            try {
                this.ctx = new (window.AudioContext || window.webkitAudioContext)();
                window.sharedBGMAudioContext = this.ctx;
                console.log('BGM Service: 创建新的 AudioContext');
            } catch (error) {
                console.error('BGM Service: 创建 AudioContext 失败:', error);
                return;
            }
        } else {
            this.ctx = window.sharedBGMAudioContext;
            console.log('BGM Service: 复用现有 AudioContext');
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
                console.warn('BGM Service: 解析页面配置失败:', e);
                this.pageConfigs = {};
            }
        }

        // 设置默认页面配置
        this.setDefaultPageConfigs();

        // 设置用户交互解锁
        this.setupUserInteractionUnlock();

        console.log('BGM Service: 初始化完成，曲目数量:', this.tracks.length);
    }

    setupUserInteractionUnlock() {
        if (window.bgmUnlocked) return;

        const unlock = () => {
            if (this.ctx && this.ctx.state === 'suspended') {
                this.ctx.resume().then(() => {
                    console.log('BGM Service: AudioContext 已解锁');
                    if (!this.isPlaying && this.tracks.length && this.enabled && this.currentPage) {
                        this.playPageBGM();
                    }
                });
            }

            if (!window.bgmUnlocked) {
                ['click', 'keydown', 'touchstart'].forEach(e =>
                    document.removeEventListener(e, unlock));
                window.bgmUnlocked = true;
            }
        };

        ['click', 'keydown', 'touchstart'].forEach(e =>
            document.addEventListener(e, unlock));
    }

    async loadTracks() {
        try {
            const res = await fetch('/api/bgm-tracks');
            this.tracks = res.ok ? await res.json() : ['bgm01.aac'];
            console.log('BGM Service: 加载曲目列表:', this.tracks);
        } catch (error) {
            console.warn('BGM Service: 加载曲目失败:', error);
            this.tracks = ['bgm01.aac'];
        }
    }

    setDefaultPageConfigs() {
        const pages = ['index', 'chat', 'story', 'story_chat', 'custom_character', 'select_character', 'settings', 'about', 'resource_management'];
        pages.forEach(page => {
            if (!this.pageConfigs[page]) {
                this.pageConfigs[page] = {
                    track: 'random',
                    enabled: true
                };
            }
        });
    }

    setCurrentPage(page) {
        if (this.currentPage === page) {
            console.log(`BGM Service: 页面未变化 (${page})，跳过重新播放`);
            return;
        }

        console.log(`BGM Service: 切换页面 ${this.currentPage} -> ${page}`);
        this.currentPage = page;

        // 延迟执行，避免页面切换时的竞态条件
        clearTimeout(this.pageChangeTimeout);
        this.pageChangeTimeout = setTimeout(() => {
            this.playPageBGM();
        }, 200);
    }

    async playPageBGM() {
        if (!this.currentPage || !this.enabled) {
            console.log('BGM Service: 页面未设置或BGM已禁用');
            return;
        }

        const config = this.pageConfigs[this.currentPage];
        if (!config || !config.enabled || config.track === 'off') {
            console.log(`BGM Service: 页面 ${this.currentPage} BGM已禁用`);
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

        if (page === this.currentPage) {
            this.playPageBGM();
        }
    }

    getAvailablePages() {
        return ['index', 'chat', 'story', 'story_chat', 'custom_character', 'select_character', 'settings', 'about', 'resource_management'];
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
            'about': '关于页面',
            'resource_management': '资源管理'
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
        if (!this.enabled) {
            console.log('BGM Service: BGM已禁用，跳过播放');
            return;
        }

        // 防重复播放检查
        const now = Date.now();
        if (now - this.lastPlayTime < this.playCooldown) {
            console.log(`BGM Service: 播放冷却中，跳过: ${trackName}`);
            return;
        }

        // 如果正在播放相同的曲目，不需要重新播放
        if (this.isPlaying && this.currentTrack === trackName) {
            console.log(`BGM Service: 已在播放 ${trackName}，跳过重复播放`);
            return;
        }

        // 如果有正在进行的播放操作，等待完成
        if (this.playingPromise) {
            console.log('BGM Service: 等待当前播放操作完成');
            await this.playingPromise;
        }

        // 创建播放Promise
        this.playingPromise = this._doPlayTrack(trackName);

        try {
            await this.playingPromise;
        } finally {
            this.playingPromise = null;
        }
    }

    async _doPlayTrack(trackName) {
        // 确保停止当前播放
        this.stop();

        try {
            console.log(`BGM Service: 开始加载 ${trackName}`);
            this.buffer = await this.fetchAndDecode(trackName);
            this.source = this.ctx.createBufferSource();
            this.source.buffer = this.buffer;
            
            // 检查当前页面配置是否为随机播放
            const config = this.pageConfigs[this.currentPage];
            const isRandomMode = config && config.track === 'random';
            
            if (isRandomMode) {
                // 随机模式下不循环，播放完毕后播放下一首
                this.source.loop = false;
                // 监听播放结束事件
                this.source.onended = () => {
                    if (this.isPlaying && this.enabled) {
                        console.log(`BGM Service: ${trackName} 播放完毕，播放下一首随机歌曲`);
                        setTimeout(() => {
                            this.playRandom();
                        }, 500); // 短暂延迟避免快速切换
                    }
                };
            } else {
                // 非随机模式下循环播放
                this.source.loop = true;
            }

            this.gainNode = this.ctx.createGain();
            this.gainNode.gain.value = this.volume;

            this.source.connect(this.gainNode).connect(this.ctx.destination);
            this.source.start();
            this.isPlaying = true;
            this.currentTrack = trackName;
            this.lastPlayTime = Date.now();
            console.log(`BGM Service: 开始播放 ${trackName} (循环: ${this.source.loop})`);
        } catch (error) {
            console.error('BGM Service: 播放失败:', error);
            this.isPlaying = false;
            this.currentTrack = null;
        }
    }

    cleanup() {
        console.log('BGM Service: 开始清理');
        clearTimeout(this.pageChangeTimeout);
        this.stop();
        this.source = null;
        this.gainNode = null;
        this.buffer = null;
        this.isPlaying = false;
    }

    async playRandom() {
        if (!this.enabled || !this.tracks.length) return;
        
        // 如果只有一首歌，直接播放
        if (this.tracks.length === 1) {
            await this.playTrack(this.tracks[0]);
            return;
        }
        
        // 选择一首与上次不同的随机歌曲
        let randomTrack;
        let attempts = 0;
        const maxAttempts = 10; // 防止无限循环
        
        do {
            const randomIndex = Math.floor(Math.random() * this.tracks.length);
            randomTrack = this.tracks[randomIndex];
            attempts++;
        } while (randomTrack === this.lastRandomTrack && attempts < maxAttempts);
        
        // 记录这次播放的歌曲
        this.lastRandomTrack = randomTrack;
        
        console.log(`BGM Service: 随机选择歌曲 ${randomTrack} (上次: ${this.currentTrack})`);
        await this.playTrack(randomTrack);
    }

    pause() {
        if (!this.ctx || this.ctx.state === 'suspended') return;
        this.ctx.suspend();
        this.isPlaying = false;
        console.log('BGM Service: 暂停播放');
    }

    resume() {
        if (!this.enabled || !this.ctx) return;
        this.ctx.resume().then(() => {
            this.isPlaying = true;
            console.log('BGM Service: 恢复播放');
        });
    }

    stop() {
        if (this.source) {
            try {
                this.source.stop();
                console.log(`BGM Service: 停止播放 ${this.currentTrack}`);
            } catch (e) {
                console.warn('BGM Service: 停止播放时出错:', e);
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
        console.log(`BGM Service: 设置音量 ${Math.round(this.volume * 100)}%`);
    }

    getVolume() { return this.volume; }
    getPlayingState() { return this.isPlaying; }
    getCurrentTrack() { return this.currentTrack; }
    getAvailableTracks() { return [...this.tracks]; }
    async refreshTracks() { await this.loadTracks(); }
}



// 全局初始化 - 确保只创建一个实例
(function initBGMService() {
    if (window.bgmServiceInitialized) {
        console.log('BGM Service: 已初始化，跳过');
        return;
    }

    window.bgmServiceInitialized = true;

    if (!window.bgmService) {
        window.bgmService = new BGMService();

        // 页面卸载时清理
        window.addEventListener('beforeunload', () => {
            if (window.bgmService) {
                window.bgmService.cleanup();
            }
        });

        console.log('BGM Service: 全局实例已创建');
    }
})();