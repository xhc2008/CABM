/**
 * 设置服务
 * 管理应用设置的前端逻辑
 */
class SettingsService {
    constructor() {
        this.settings = {};
        this.init();
    }

    async init() {
        await this.loadSettings();
        this.applySettings();
    }

    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            if (response.ok) {
                this.settings = await response.json();
            } else {
                console.error('获取设置失败:', response.statusText);
                this.settings = this.getDefaultSettings();
            }
        } catch (error) {
            console.error('加载设置失败:', error);
            this.settings = this.getDefaultSettings();
        }
    }

    async saveSettings(newSettings) {
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newSettings)
            });

            const result = await response.json();
            if (result.success) {
                this.settings = { ...this.settings, ...newSettings };
                this.applySettings();
                return true;
            } else {
                console.error('保存设置失败:', result.error);
                return false;
            }
        } catch (error) {
            console.error('保存设置失败:', error);
            return false;
        }
    }

    getDefaultSettings() {
        return {
            storage: {
                type: 'json',
                vector_db_path: 'data/memory',
                chat_history_path: 'data/history'
            },
            audio: {
                bgm_volume: 0.5,
                bgm_enabled: true,
                bgm_folder: 'static/bgm'
            },
            ui: {
                show_logo: true,
                theme: 'default'
            }
        };
    }

    applySettings() {
        // 应用背景音乐设置
        if (window.bgmService) {
            window.bgmService.setVolume(this.settings.audio?.bgm_volume || 0.5);
            if (this.settings.audio?.bgm_enabled) {
                if (!window.bgmService.getPlayingState()) {
                    window.bgmService.playRandom();
                }
            } else {
                window.bgmService.stop();
            }
        }

        // 应用Logo显示设置
        const showLogo = this.settings.ui?.show_logo !== false;
        localStorage.setItem('showLogoSplash', showLogo);

        // 应用主题设置
        this.applyTheme(this.settings.ui?.theme || 'default');
    }

    applyTheme(theme) {
        const body = document.body;
        
        // 移除所有主题类
        body.classList.remove('theme-default', 'theme-sci-fi');
        
        // 应用新主题
        switch (theme) {
            case 'sci-fi':
                body.classList.add('theme-sci-fi');
                break;
            case 'default':
            default:
                body.classList.add('theme-default');
                break;
        }
    }

    getSetting(section, key, defaultValue = null) {
        return this.settings[section]?.[key] ?? defaultValue;
    }

    setSetting(section, key, value) {
        if (!this.settings[section]) {
            this.settings[section] = {};
        }
        this.settings[section][key] = value;
    }

    getAllSettings() {
        return { ...this.settings };
    }
}

// 创建全局设置服务实例
window.settingsService = new SettingsService();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SettingsService;
}
