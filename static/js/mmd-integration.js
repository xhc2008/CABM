import { initMMDCharacterSystem, loadCharacter, playEmotionAnimation, dispose as disposeMMD, isCharacterSystemInitialized } from './mmd-character.js';
import { getCurrentCharacter } from './character-service.js';

const STORAGE_KEY = 'useMMDPortrait';

function getToggleState() {
    return localStorage.getItem(STORAGE_KEY) === 'true';
}

function setToggleState(enabled) {
    localStorage.setItem(STORAGE_KEY, enabled ? 'true' : 'false');
}

function showMMDCanvas(show) {
    const canvas = document.getElementById('mmdCanvas');
    const img = document.getElementById('characterImage');
    if (!canvas) {
        console.error('[MMD] 未找到 mmdCanvas 容器');
        return;
    }
    if (!img) {
        console.warn('[MMD] 未找到 characterImage，可能已被隐藏或模板变更');
    }
    canvas.style.display = show ? 'block' : 'none';
    if (img) img.style.display = show ? 'none' : 'block';
}

async function enableMMD() {
    try {
        console.log('[MMD] 准备启用MMD');
        if (typeof THREE === 'undefined') {
            console.error('[MMD] THREE 未加载，请检查 /static/plugin/three 路径及脚本标签顺序');
            alert('MMD依赖未加载（THREE未定义）。请检查静态脚本是否可访问。');
            return;
        }
        if (!THREE.MMDLoader) {
            console.error('[MMD] THREE.MMDLoader 未加载，请检查 MMDLoader 脚本是否正确引入');
            alert('MMD依赖未加载（MMDLoader未定义）。请检查静态脚本是否可访问。');
            return;
        }

        // 初始化渲染器
        if (!isCharacterSystemInitialized()) {
            console.log('[MMD] 初始化渲染系统...');
            initMMDCharacterSystem('mmdCanvas');
        }

        // 加载当前角色对应的MMD（按角色ID，缺省回退 Silver_Wolf）
        const character = getCurrentCharacter();
        const characterId = character?.id || 'Silver_Wolf';
        console.log('[MMD] 加载角色:', characterId);

        await loadCharacter(characterId);
        playEmotionAnimation('idle');
        showMMDCanvas(true);
        console.log('[MMD] 启用完成');
    } catch (e) {
        console.error('[MMD] 启用失败:', e);
        alert('启用MMD失败：' + (e?.message || e));
        showMMDCanvas(false);
    }
}

function disableMMD() {
    console.log('[MMD] 关闭MMD并恢复图片立绘');
    try {
        disposeMMD();
    } catch (e) {
        console.warn('[MMD] 关闭时出现问题:', e);
    }
    showMMDCanvas(false);
}

function applyInitialState() {
    const enabled = getToggleState();
    console.log('[MMD] 初始化状态 useMMDPortrait =', enabled);
    if (enabled) enableMMD(); else disableMMD();
}

// 提供全局调试方法
window.__MMD__ = {
    enable: () => { setToggleState(true); enableMMD(); },
    disable: () => { setToggleState(false); disableMMD(); },
    state: () => getToggleState()
};

// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    console.log('[MMD] mmd-integration.js 已加载，开始应用初始状态');
    applyInitialState();
}); 