/**
 * MMD角色管理模块
 * 管理不同角色的MMD模型、动画和表情
 */

import { 
    initMMDRenderer, 
    loadMMDModel, 
    loadAnimation, 
    playExpression,
    setCameraPosition,
    setCameraTarget,
    dispose as disposeRenderer
} from './mmd-renderer.js';

// 角色配置
const characterConfigs = {
    'Silver_Wolf': {
        model: '/static/models/characters/Silver_Wolf/Silver_Wolf.pmx',
        animations: {
            idle: '/static/models/animations/idle.vmd',
            happy: '/static/models/animations/happy.vmd',
            sad: '/static/models/animations/sad.vmd',
            angry: '/static/models/animations/angry.vmd',
            surprised: '/static/models/animations/surprised.vmd'
        },
        expressions: {
            normal: 'normal',
            happy: 'happy',
            sad: 'sad',
            angry: 'angry',
            surprised: 'surprised'
        },
        camera: {
            position: [0, 1.8, 2.4],
            target: [0, 1.4, 0]
        }
    },
    'Collei': {
        model: '/static/models/characters/Collei/Collei.pmx',
        animations: {
            idle: '/static/models/animations/idle.vmd',
            happy: '/static/models/animations/happy.vmd',
            sad: '/static/models/animations/sad.vmd',
            shy: '/static/models/animations/shy.vmd'
        },
        expressions: {
            normal: 'normal',
            happy: 'happy',
            sad: 'sad',
            shy: 'shy'
        },
        camera: {
            position: [0, 10, 25],
            target: [0, 10, 0]
        }
    },
    'Elysia': {
        model: '/static/models/characters/Elysia/Elysia.pmx',
        animations: {
            idle: '/static/models/animations/idle.vmd',
            happy: '/static/models/animations/happy.vmd',
            elegant: '/static/models/animations/elegant.vmd',
            playful: '/static/models/animations/playful.vmd'
        },
        expressions: {
            normal: 'normal',
            happy: 'happy',
            elegant: 'elegant',
            playful: 'playful'
        },
        camera: {
            position: [0, 10, 25],
            target: [0, 10, 0]
        }
    },
    'lingyin': {
        model: '/static/models/characters/lingyin/lingyin.pmx',
        animations: {
            idle: '/static/models/animations/idle.vmd',
            happy: '/static/models/animations/happy.vmd',
            elegant: '/static/models/animations/elegant.vmd',
            playful: '/static/models/animations/playful.vmd'
        },
        expressions: {
            normal: 'normal',
            happy: 'happy',
            elegant: 'elegant',
            playful: 'playful'
        },
        camera: {
            position: [0, 10, 25],
            target: [0, 10, 0]
        }
    }
};

// 当前角色状态
let currentCharacter = null;
let currentAnimation = null;
let isInitialized = false;

// 初始化MMD角色系统
export function initMMDCharacterSystem(containerId) {
    if (isInitialized) {
        console.warn('MMD角色系统已经初始化');
        return;
    }
    
    console.log('正在初始化MMD角色系统...');
    
    // 初始化渲染器
    initMMDRenderer(containerId);
    
    isInitialized = true;
    console.log('MMD角色系统初始化完成');
}

// 加载角色
export function loadCharacter(characterId) {
    if (!isInitialized) {
        console.error('MMD角色系统未初始化');
        return Promise.reject('系统未初始化');
    }
    
    const config = characterConfigs[characterId];
    if (!config) {
        console.error('未找到角色配置:', characterId);
        return Promise.reject('角色配置不存在');
    }
    
    console.log('正在加载角色:', characterId);
    
    return new Promise((resolve, reject) => {
        loadMMDModel(config.model, (model) => {
            currentCharacter = {
                id: characterId,
                config: config,
                model: model
            };
            
            // 设置相机
            if (config.camera) {
                setCameraPosition(...config.camera.position);
                setCameraTarget(...config.camera.target);
            }
            
            // 加载默认动画
            if (config.animations.idle) {
                loadAnimation(config.animations.idle, (animation) => {
                    currentAnimation = 'idle';
                    console.log('角色加载完成:', characterId);
                    resolve(currentCharacter);
                });
            } else {
                console.log('角色加载完成:', characterId);
                resolve(currentCharacter);
            }
        });
    });
}

// 播放动画
export function playAnimation(animationName) {
    if (!currentCharacter) {
        console.error('没有加载的角色');
        return;
    }
    
    const config = currentCharacter.config;
    const animationPath = config.animations[animationName];
    
    if (!animationPath) {
        console.error('未找到动画:', animationName);
        return;
    }
    
    console.log('播放动画:', animationName);
    
    loadAnimation(animationPath, (animation) => {
        currentAnimation = animationName;
    });
}

// 播放表情
export function playCharacterExpression(expressionName) {
    if (!currentCharacter) {
        console.error('没有加载的角色');
        return;
    }
    
    const config = currentCharacter.config;
    const expression = config.expressions[expressionName];
    
    if (!expression) {
        console.error('未找到表情:', expressionName);
        return;
    }
    
    console.log('播放表情:', expressionName);
    playExpression(expression);
}

// 根据情感状态播放相应的动画和表情
export function playEmotionAnimation(emotion) {
    if (!currentCharacter) {
        console.error('没有加载的角色');
        return;
    }
    
    // 情感到动画的映射
    const emotionMap = {
        'happy': { animation: 'happy', expression: 'happy' },
        'sad': { animation: 'sad', expression: 'sad' },
        'angry': { animation: 'angry', expression: 'angry' },
        'surprised': { animation: 'surprised', expression: 'surprised' },
        'shy': { animation: 'shy', expression: 'shy' },
        'elegant': { animation: 'elegant', expression: 'elegant' },
        'playful': { animation: 'playful', expression: 'playful' }
    };
    
    const emotionConfig = emotionMap[emotion];
    if (emotionConfig) {
        if (emotionConfig.animation) {
            playAnimation(emotionConfig.animation);
        }
        if (emotionConfig.expression) {
            playCharacterExpression(emotionConfig.expression);
        }
    } else {
        // 默认回到idle状态
        playAnimation('idle');
        playCharacterExpression('normal');
    }
}

// 获取当前角色
export function getCurrentCharacter() {
    return currentCharacter;
}

// 获取当前动画
export function getCurrentAnimation() {
    return currentAnimation;
}

// 获取角色配置
export function getCharacterConfig(characterId) {
    return characterConfigs[characterId];
}

// 获取所有可用角色
export function getAvailableCharacters() {
    return Object.keys(characterConfigs);
}

// 检查角色是否存在
export function hasCharacter(characterId) {
    return characterConfigs.hasOwnProperty(characterId);
}

// 设置相机位置
export function setCharacterCamera(x, y, z) {
    setCameraPosition(x, y, z);
}

// 设置相机目标
export function setCharacterCameraTarget(x, y, z) {
    setCameraTarget(x, y, z);
}

// 重置到默认相机位置
export function resetCamera() {
    if (currentCharacter && currentCharacter.config.camera) {
        const camera = currentCharacter.config.camera;
        setCameraPosition(...camera.position);
        setCameraTarget(...camera.target);
    }
}

// 清理资源
export function dispose() {
    currentCharacter = null;
    currentAnimation = null;
    disposeRenderer();
    isInitialized = false;
    console.log('MMD角色系统已清理');
}

// 检查是否已初始化
export function isCharacterSystemInitialized() {
    return isInitialized;
} 