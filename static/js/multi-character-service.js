/**
 * 多角色对话服务
 * 处理多角色故事中的角色切换、立绘显示等功能
 */

// 当前屏幕上的角色状态
let currentCharacters = {
    left: null,    // 左侧角色
    right: null,   // 右侧角色
    center: null   // 中央角色（单角色时使用）
};

// 角色立绘元素
let characterElements = {
    left: null,
    right: null,
    center: null
};

// 新增：左右角色外层容器（用于承载缩放与位置调整）
let characterContainers = {
    left: null,
    right: null
};

// 角色信息缓存
let characterCache = new Map();

// 正在进行的请求缓存，避免重复请求
let pendingRequests = new Map();
import {
    setCurrentCharacter,
    updateCharacterImage
} from './character-service.js';

/**
 * 初始化多角色服务
 */
export function initMultiCharacterService() {
    // 检查是否是多角色故事并且是剧情模式
    const isStoryPage = window.location.pathname.includes('story');
    const isMultiCharacter = window.storyData?.characters?.list?.length > 1 || 
                            window.storyData?.characters?.length > 1;
    
    if (!isStoryPage || !isMultiCharacter) {
        console.log('非剧情模式或单角色故事，不初始化多角色服务');
        return;
    }
    
    console.log('多角色故事，初始化多角色服务');
    
    // 设置多角色标志
    window.isMultiCharacterStory = true;
    
    // 获取角色容器和元素
    characterElements.left = document.getElementById('characterLeft');
    characterElements.right = document.getElementById('characterRight');
    characterElements.center = document.getElementById('characterCenter');

    // 创建左右独立外层容器，并将原有元素迁移进去
    const rootContainer = document.querySelector('.character-container');
    if (rootContainer) {
        const parent = rootContainer.parentElement || document.body;
        // 左容器
        if (!document.querySelector('.character-container-left')) {
            const leftContainer = document.createElement('div');
            leftContainer.className = 'character-container-left';
            leftContainer.style.position = 'absolute';
            leftContainer.style.display = 'flex';
            leftContainer.style.opacity = '0';
            parent.appendChild(leftContainer);
        }
        // 右容器
        if (!document.querySelector('.character-container-right')) {
            const rightContainer = document.createElement('div');
            rightContainer.className = 'character-container-right';
            rightContainer.style.position = 'absolute';
            rightContainer.style.display = 'flex';
            rightContainer.style.opacity = '0';
            parent.appendChild(rightContainer);
        }

        characterContainers.left = document.querySelector('.character-container-left');
        characterContainers.right = document.querySelector('.character-container-right');

        // 将原始左右元素放入对应容器
        if (characterElements.left && characterContainers.left && characterElements.left.parentElement !== characterContainers.left) {
            characterContainers.left.appendChild(characterElements.left);
        }
        if (characterElements.right && characterContainers.right && characterElements.right.parentElement !== characterContainers.right) {
            characterContainers.right.appendChild(characterElements.right);
        }
    }
    
    // 隐藏中央角色（单角色模式）
    if (characterElements.center) {
        characterElements.center.style.display = 'none';
    }
    // switchToCharacter("Silver_Wolf")
    // switchToCharacter("Collei")
    // 显示左右角色（多角色模式）的逻辑已移动到 showCharacterAt 函数中
    setTimeout(() => {
        Object.entries(currentCharacters).forEach(([position, character]) => {
            if (character && (position === 'left' || position === 'right')) {
                const container = characterContainers[position];
                applyCharacterScaling(container, character.character);
                applyCharacterPosition(container, character.character, position);
            }
        });
    }, 100);
    console.log('多角色服务已初始化');
}

/**
 * 切换到指定角色
 * @param {string} characterId - 角色ID
 * @param {string} characterName - 角色名称
 */
export function switchToCharacter(characterId, characterName, characterMood = null) {
    console.log(`切换到角色: ${characterName} (${characterId})`);
    
    // 检查是否已经是当前说话角色
    const currentSpeakingChar = findCurrentSpeakingCharacter();
    if (currentSpeakingChar && currentSpeakingChar.id === characterId) {
        console.log(`角色 ${characterName} 已经是当前说话角色`);
        return;
    }
    // 获取角色配置
    fetch(`/api/characters/${characterId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const character = data.character;
                console.log("更新current角色", character);
                setCurrentCharacter(character);
                showCharacter(characterId, character, characterName, characterMood);
            }
        })
        .catch(error => {
            console.error('获取角色配置失败:', error);
        });
}

// 修改后：显示角色
function showCharacter(characterId, character, characterName, characterMood = null) {
    console.log(`显示角色: ${characterName} (${characterId})`);
    
    // 检查当前屏幕上的角色数量
    const activeCharacters = Object.values(currentCharacters).filter(char => char !== null);
    
    // 如果没有角色，随机显示在一侧
    if (activeCharacters.length === 0) {
        const side = Math.random() < 0.5 ? 'left' : 'right';
        showCharacterAt(side, characterId, character, characterName, characterMood);
        return;
    }
    //避免在两侧同时出现
    let currentChar = currentCharacters['left'];
    if (currentChar && currentChar.id === characterId) {
        console.log(`角色 ${characterName} 已经在left位置`);
        showCharacterAt('left', characterId, character, characterName, characterMood);
        return;
    }
    currentChar = currentCharacters['right'];
    if (currentChar && currentChar.id === characterId) {
        console.log(`角色 ${characterName} 已经在right位置`);
        showCharacterAt('right', characterId, character, characterName, characterMood);
        return;
    }
    // 如果只有一个角色，新角色显示在另一侧
    if (activeCharacters.length === 1) {
        const existingPosition = Object.keys(currentCharacters).find(pos => currentCharacters[pos] !== null);
        const targetPosition = existingPosition === 'left' ? 'right' : 'left';
        showCharacterAt(targetPosition, characterId, character, characterName, characterMood);
        return;
    }
    
    // 如果已有两个角色，随机替换一侧
    const side = Math.random() < 0.5 ? 'left' : 'right';
    showCharacterAt(side, characterId, character, characterName, characterMood);
}
/**
 * 应用角色缩放率（多角色模式）
 */
function applyCharacterScaling(targetContainer, character) {
    if (!targetContainer || !character) return;

    const scaleValue = typeof character.scale_rate !== 'undefined'
        ? character.scale_rate / 100
        : 1;

    console.log(`应用角色缩放(容器): ${character.name}, 缩放率: ${scaleValue}`);

    // 与单角色一致：在容器上应用translate+scale，保持以容器为中心
    const baseTranslate = targetContainer.classList.contains('character-container-right')
        ? 'translate(-50%, -50%)'
        : 'translate(-50%, -50%)';
    targetContainer.style.transform = `${baseTranslate} scale(${scaleValue})`;
    targetContainer.style.setProperty('--base-scale', scaleValue);

    const imgElement = targetContainer.querySelector('.character-img');
    if (imgElement) {
        imgElement.style.transformOrigin = 'center center';
    }
}

/**
 * 应用角色位置调整（多角色模式）
 */
function applyCharacterPosition(targetContainer, character, position) {
    if (!targetContainer || !character) return;

    const positionAdjustment = typeof character.calib !== 'undefined'
        ? character.calib
        : 0;

    console.log(`应用角色位置调整(容器): ${character.name}, 调整值: ${positionAdjustment}`);

    // 与单角色一致：以容器top为基准50%，做百分比偏移
    const baseTop = 50;
    const adjustedTop = baseTop + positionAdjustment;
    targetContainer.style.top = `${adjustedTop}%`;

    // X 坐标由左右容器的CSS控制（left:25% / 75%），此处不改动
}
/**
 * 在指定位置显示角色
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @param {string} characterName - 角色名称
 */
function showCharacterAt(position, characterId, character, characterName, characterMood = null) {
    const element = characterElements[position];
    const container = position === 'left' ? characterContainers.left : characterContainers.right;
    if (!element || !container) {
        console.error(`未找到 ${position} 位置的角色元素`);
        return;
    }
    
    // 确保容器和内部元素显示
    container.style.display = 'flex';
    container.style.position = 'absolute';
    container.style.opacity = container.style.opacity || '0';
    element.style.display = 'flex';
    element.style.position = 'relative';
    
    // 检查是否已经是同一角色在同一位置
    // const currentChar = currentCharacters[position];
    // if (currentChar && currentChar.id === characterId) {
    //     console.log(`角色 ${characterName} 已经在 ${position} 位置，无需更新`);
    //     return;
    // }
    smoothCharacterTransition(characterId, position, characterMood);
    // 获取角色立绘URL
    // const imageUrl = getCharacterImageUrl(characterId, character);
    
    // 更新角色状态
    currentCharacters[position] = {
        id: characterId,
        name: characterName,
        character: character
    };
    
    // 设置立绘
    // const imgElement = element.querySelector('.character-img');
    // if (imgElement) {
    //     imgElement.src = imageUrl;
    //     imgElement.alt = characterName;
        
    //     // 处理图片加载错误
    //     imgElement.onerror = function() {
    //         console.error(`角色图片加载失败: ${imageUrl}`);
    //         this.src = '/static/images/default.svg';
    //     };
        
    //     // 图片加载完成后添加呼吸效果和应用缩放
    //     imgElement.onload = function() {
    //         this.classList.add('character-breathing');
            
    //         // 应用角色缩放率（多角色模式）
    //         applyCharacterScaling(element, character);
            
    //         // 应用角色位置调整（多角色模式）
    //         applyCharacterPosition(element, character, position);
    //     };
    // }
    
    // 立即应用缩放和位置（即使图片未加载）
    applyCharacterScaling(container, character);
    applyCharacterPosition(container, character, position);
    
    // 显示动画
    container.style.opacity = '1';
    
    console.log(`角色 ${characterName} 已显示在 ${position} 容器，缩放率: ${character.scale_rate || 100}%, 位置调整: ${character.calib || 0}`);
}

/**
 * 将角色从一个位置移动到另一个位置
 * @param {string} fromPosition - 源位置
 * @param {string} toPosition - 目标位置
 * @param {Object} characterData - 角色数据
 */ 
function moveCharacterFromTo(fromPosition, toPosition, characterData) {
    const fromElement = characterElements[fromPosition];
    const toElement = characterElements[toPosition];
    
    if (!fromElement || !toElement || !characterData) return;
    
    // 复制立绘到新位置
    const fromImg = fromElement.querySelector('.character-img');
    const toImg = toElement.querySelector('.character-img');
    if (fromImg && toImg) {
        toImg.src = fromImg.src;
        toImg.alt = fromImg.alt;
    }
    
    // 更新角色状态
    currentCharacters[toPosition] = characterData;
    currentCharacters[fromPosition] = null;
    
    // 隐藏原位置
    fromElement.style.opacity = '0';
    fromImg.src = '';
    
    // 显示新位置
    toElement.style.opacity = '1';
    
    console.log(`角色从 ${fromPosition} 移动到 ${toPosition}`);
}

/**
 * 获取角色立绘URL
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @returns {string} 立绘URL
 */
function getCharacterImageUrl(characterId, character, mood = null) {
    // 优先使用角色配置中的立绘
    if (character.image_url) {
        return character.image_url;
    }
    
    // 使用角色配置中的 image 目录（若有），否则回退到默认路径
    const number = (() => {
        const n = parseInt(mood, 10);
        return isNaN(n) || n <= 0 ? 1 : n;
    })();
    // if (character.image) {
    //     const base = character.image.endsWith('/') ? character.image : `${character.image}/`;
    //     return `${base}${number}.png`;
    // }
    return `/static/images/${characterId}/${number}.png`;
}

/**
 * 显示角色回复状态
 * @param {string} characterName - 角色名称
 */
// 修改后：显示角色回复状态（移除发光效果）
export function showCharacterResponse(characterID) {
    console.log(`${characterID} 正在回复...`);
    // 移除发光效果，留到后续添加
}

// 修改后：更新角色回复内容（移除发光效果）
export function updateCharacterResponse(content) {
    // 注意：文本内容的显示由主流处理器(streamProcessor)处理
    // 这里主要处理角色特定的视觉效果
    console.log('角色回复内容已更新:', content.substring(0, 50) + '...');
}

/**
 * 查找当前正在说话的角色
 * @returns {Object|null} 角色信息和位置
 */
function findCurrentSpeakingCharacter() {
    // 简单实现：返回最近显示的角色
    // 更复杂的实现可以基于角色名称匹配或其他逻辑
    for (const [position, character] of Object.entries(currentCharacters)) {
        if (character !== null) {
            return { ...character, position };
        }
    }
    return null;
}

/**
 * 完成角色回复
 */
export function completeCharacterResponse() {
    console.log('角色回复完成');
    
    // 移除所有角色的发光效果
}

/**
 * 根据名称查找角色
 * @param {string} characterName - 角色名称
 * @returns {Object|null} 角色信息和位置
 */
function findCharacterByName(characterName) {
    for (const [position, character] of Object.entries(currentCharacters)) {
        if (character && character.name === characterName) {
            return { ...character, position };
        }
    }
    return null;
}

/**
 * 根据ID获取角色完整信息（从后端API获取，带缓存优化）
 * @param {string} characterId - 角色ID
 * @returns {Promise<Object|null>} 角色完整信息
 */
export async function getCharacterById(characterId) {
    if (!characterId) {
        return null;
    }
    
    // 检查缓存
    if (characterCache.has(characterId)) {
        console.log(`从缓存获取角色信息: ${characterId}`);
        return characterCache.get(characterId);
    }
    
    // 检查是否有正在进行的请求
    if (pendingRequests.has(characterId)) {
        console.log(`等待正在进行的请求: ${characterId}`);
        return await pendingRequests.get(characterId);
    }
    
    // 创建新的请求
    const requestPromise = (async () => {
        try {
            console.log(`发起API请求获取角色信息: ${characterId}`);
            const response = await fetch(`/api/characters/${characterId}`);
            const data = await response.json();
            
            if (data.success) {
                // 缓存结果
                characterCache.set(characterId, data.character);
                console.log(`角色信息已缓存: ${characterId} - ${data.character.name}`);
                return data.character;
            } else {
                console.error('获取角色信息失败:', data.error);
                return null;
            }
        } catch (error) {
            console.error('获取角色信息时发生错误:', error);
            return null;
        } finally {
            // 清除正在进行的请求记录
            pendingRequests.delete(characterId);
        }
    })();
    
    // 记录正在进行的请求
    pendingRequests.set(characterId, requestPromise);
    
    return await requestPromise;
}

/**
 * 根据ID查找角色基本信息（从故事数据中，仅用于快速查找）
 * @param {string} characterId - 角色ID
 * @returns {Object|null} 角色基本信息
 */
export function getCharacterBasicInfo(characterId) {
    if (!window.storyData?.characters) {
        return null;
    }
    
    // 尝试从角色列表中找到对应的角色
    if (window.storyData.characters.list) {
        return window.storyData.characters.list.find(char => char.id === characterId);
    } else if (Array.isArray(window.storyData.characters)) {
        return window.storyData.characters.find(char => char.id === characterId);
    }
    
    return null;
}
// 新增：平滑切换角色显示
function smoothCharacterTransition(newCharacterId, position, characterMood = null) {
    const element = characterElements[position];
    const container = position === 'left' ? characterContainers.left : characterContainers.right;
    if (!element || !container) return;
    // 直接显示新角色（无需动画）
    showNewCharacter(newCharacterId, position, characterMood);
}
function showNewCharacter(characterId, position, characterMood = null) {
    const element = characterElements[position];
    const container = position === 'left' ? characterContainers.left : characterContainers.right;
    if (!element || !container) return;
    
    // 获取新角色信息
    getCharacterById(characterId).then(character => {
        if (character) {
            const imgElement = element.querySelector('.character-img');
            if (imgElement) {
                imgElement.src = getCharacterImageUrl(characterId, character, characterMood);
                imgElement.alt = character.name;
                
                imgElement.onerror = function() {
                    console.error(`角色图片加载失败: ${imgElement.src}`);
                    this.src = '/static/images/default.svg';
                };
                
                imgElement.onload = function() {
                    // 应用缩放和位置
                    applyCharacterScaling(container, character);
                    applyCharacterPosition(container, character, position);
                    
                    container.style.opacity = '1';
                    console.log(`角色已平滑切换: ${character.name} 在 ${position} 位置`);
                    
                    this.classList.add('character-breathing');
                };
            }
            
            // 立即应用缩放和位置（即使图片未加载）
            applyCharacterScaling(container, character);
            applyCharacterPosition(container, character, position);
            
            // 更新角色状态
            currentCharacters[position] = {
                id: characterId,
                name: character.name,
                character: character
            };
        }
    }).catch(error => {
        console.error('获取角色信息失败:', error);
    });
}
/**
 * 清除所有角色
 */
// 修改后：清除所有角色，使用现有的HTML元素
export function clearAllCharacters() {
    // 隐藏并重置左右容器
    Object.values(characterContainers).forEach(container => {
        if (container) {
            container.style.opacity = '0';
            container.style.transform = 'translate(-50%, -50%) scale(1)';
            const img = container.querySelector('.character-img');
            if (img) {
                img.src = '/static/images/default.svg';
            }
        }
    });
    
    currentCharacters = {
        left: null,
        right: null,
        center: null
    };
    
    console.log('已清除所有角色');
}

/**
 * 清除角色信息缓存
 * @param {string} characterId - 可选，指定要清除的角色ID，不传则清除所有缓存
 */
export function clearCharacterCache(characterId = null) {
    if (characterId) {
        characterCache.delete(characterId);
        pendingRequests.delete(characterId);
        console.log(`已清除角色缓存: ${characterId}`);
    } else {
        characterCache.clear();
        pendingRequests.clear();
        console.log('已清除所有角色缓存');
    }
}

/**
 * 获取缓存统计信息
 * @returns {Object} 缓存统计
 */
export function getCacheStats() {
    return {
        cachedCharacters: characterCache.size,
        pendingRequests: pendingRequests.size,
        cachedIds: Array.from(characterCache.keys())
    };
}

// 暴露给全局使用
window.switchToCharacter = switchToCharacter;
window.showCharacterResponse = showCharacterResponse;
window.updateCharacterResponse = updateCharacterResponse;
window.completeCharacterResponse = completeCharacterResponse;
window.getCharacterById = getCharacterById;
window.getCharacterBasicInfo = getCharacterBasicInfo;
window.clearCharacterCache = clearCharacterCache;
window.getCacheStats = getCacheStats;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initMultiCharacterService);