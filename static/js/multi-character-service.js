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

// 角色信息缓存
let characterCache = new Map();

// 正在进行的请求缓存，避免重复请求
let pendingRequests = new Map();
import {
    setCurrentCharacter
} from './character-service.js';
/**
 * 初始化多角色服务
 */
export function initMultiCharacterService() {
    // 检查是否是多角色故事
    const isMultiCharacter = window.storyData?.characters?.list?.length > 1 || 
                            window.storyData?.characters?.length > 1;
    
    if (!isMultiCharacter) {
        console.log('单角色故事，不初始化多角色服务');
        return;
    }
    
    console.log('多角色故事，初始化多角色服务');
    
    // 获取角色容器和元素
    characterElements.left = document.getElementById('characterLeft');
    characterElements.right = document.getElementById('characterRight');
    characterElements.center = document.getElementById('characterCenter');
    
    // 隐藏中央角色（单角色模式）
    if (characterElements.center) {
        characterElements.center.style.display = 'none';
    }
    
    // 显示左右角色（多角色模式）
    if (characterElements.left) {
        characterElements.left.style.display = 'flex';
        // 添加呼吸效果
        const leftImg = characterElements.left.querySelector('.character-img');
        if (leftImg) {
            leftImg.classList.add('character-breathing');
        }
    }
    if (characterElements.right) {
        characterElements.right.style.display = 'flex';
        // 添加呼吸效果
        const rightImg = characterElements.right.querySelector('.character-img');
        if (rightImg) {
            rightImg.classList.add('character-breathing');
        }
    }
    
    console.log('多角色服务已初始化');
}

/**
 * 创建角色立绘元素
 */
function createCharacterElements() {
    const chatContainer = document.querySelector('.character-container') || document.body;
    
    // 创建左侧角色元素 - 使用与单角色相同的样式
    const leftCharacter = document.createElement('div');
    leftCharacter.className = 'character-image character-left';
    leftCharacter.style.cssText = `
        position: absolute;
        left: 5%;
        bottom: 0;
        max-width: 40%;
        max-height: 80%;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: all 0.5s ease;
        z-index: 1;
        pointer-events: none;
    `;
    
    const leftImg = document.createElement('img');
    leftImg.className = 'character-img';
    leftImg.style.cssText = `
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transform-origin: center center;
    `;
    leftCharacter.appendChild(leftImg);
    
    // 创建右侧角色元素 - 使用与单角色相同的样式
    const rightCharacter = document.createElement('div');
    rightCharacter.className = 'character-image character-right';
    rightCharacter.style.cssText = `
        position: absolute;
        right: 5%;
        bottom: 0;
        max-width: 40%;
        max-height: 80%;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transition: all 0.5s ease;
        z-index: 1;
        pointer-events: none;
    `;
    
    const rightImg = document.createElement('img');
    rightImg.className = 'character-img';
    rightImg.style.cssText = `
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transform-origin: center center;
    `;
    rightCharacter.appendChild(rightImg);
    
    // 添加到现有的角色容器
    chatContainer.appendChild(leftCharacter);
    chatContainer.appendChild(rightCharacter);
    
    // 更新元素引用
    characterElements.left = leftCharacter;
    characterElements.right = rightCharacter;
    characterElements.center = null; // 多角色模式下不使用中央位置
}

/**
 * 切换到指定角色
 * @param {string} characterId - 角色ID
 * @param {string} characterName - 角色名称
 */
export function switchToCharacter(characterId, characterName) {
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
                showCharacter(characterId, character, characterName);
            }
        })
        .catch(error => {
            console.error('获取角色配置失败:', error);
        });
}

// 修改后：显示角色
function showCharacter(characterId, character, characterName) {
    console.log(`显示角色: ${characterName} (${characterId})`);
    
    // 检查当前屏幕上的角色数量
    const activeCharacters = Object.values(currentCharacters).filter(char => char !== null);
    
    // 如果没有角色，显示在左侧
    if (activeCharacters.length === 0) {
        showCharacterAt('left', characterId, character, characterName);
        return;
    }
    
    // 如果只有一个角色，新角色显示在另一侧
    if (activeCharacters.length === 1) {
        const existingPosition = Object.keys(currentCharacters).find(pos => currentCharacters[pos] !== null);
        const targetPosition = existingPosition === 'left' ? 'right' : 'left';
        showCharacterAt(targetPosition, characterId, character, characterName);
        return;
    }
    
    // 如果已有两个角色，随机替换一侧
    const side = Math.random() < 0.5 ? 'left' : 'right';
    showCharacterAt(side, characterId, character, characterName);
}

/**
 * 在指定位置显示角色
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @param {string} characterName - 角色名称
 */
// 修改后：显示角色，使用平滑过渡
function showCharacterAt(position, characterId, character, characterName) {
    const element = characterElements[position];
    if (!element) {
        console.error(`未找到 ${position} 位置的角色元素`);
        return;
    }
    
    // 检查是否已经是同一角色在同一位置
    const currentChar = currentCharacters[position];
    if (currentChar && currentChar.id === characterId) {
        console.log(`角色 ${characterName} 已经在 ${position} 位置，无需更新`);
        return;
    }
    
    // 如果有当前角色，使用平滑过渡
    if (currentChar) {
        smoothCharacterTransition(currentChar.id, characterId, position);
        return;
    }
    
    // 获取角色立绘URL
    const imageUrl = getCharacterImageUrl(characterId, character);
    
    // 更新角色状态
    currentCharacters[position] = {
        id: characterId,
        name: characterName,
        character: character
    };
    
    // 设置立绘
    const imgElement = element.querySelector('.character-img');
    if (imgElement) {
        imgElement.src = imageUrl;
        imgElement.alt = characterName;
        
        // 处理图片加载错误
        imgElement.onerror = function() {
            console.error(`角色图片加载失败: ${imageUrl}`);
            this.src = '/static/images/default.svg';
        };
        
        // 图片加载完成后添加呼吸效果
        imgElement.onload = function() {
            this.classList.add('character-breathing');
        };
    }
    
    // 显示动画
    element.style.opacity = '1';
    
    console.log(`角色 ${characterName} 已显示在 ${position} 位置`);
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
function getCharacterImageUrl(characterId, character) {
    // 优先使用角色配置中的立绘
    if (character.image_url) {
        return character.image_url;
    }
    
    // 使用默认立绘路径
    return `/static/images/${characterId}/1.png`;
}

/**
 * 显示角色回复状态
 * @param {string} characterName - 角色名称
 */
// 修改后：显示角色回复状态（移除发光效果）
export function showCharacterResponse(characterName) {
    console.log(`${characterName} 正在回复...`);
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
function smoothCharacterTransition(oldCharacterId, newCharacterId, position) {
    const element = characterElements[position];
    if (!element) return;
    console.log("平滑过渡……")
    // 获取当前角色的图片元素
    const imgElement = element.querySelector('.character-img');
    if (!imgElement) return;
    
    // 保存当前透明度
    const currentOpacity = parseFloat(element.style.opacity) || 0;
    
    // 如果当前角色已经显示，先淡出
    if (currentOpacity > 0) {
        // 淡出当前角色
        element.style.opacity = '0';
        
        // 延迟后显示新角色
        setTimeout(() => {
            showNewCharacter(newCharacterId, position);
        }, 300); // 300毫秒的淡出时间
    } else {
        // 直接显示新角色
        showNewCharacter(newCharacterId, position);
    }
}
function showNewCharacter(characterId, position) {
    const element = characterElements[position];
    if (!element) return;
    
    // 获取新角色信息
    getCharacterById(characterId).then(character => {
        if (character) {
            const imgElement = element.querySelector('.character-img');
            if (imgElement) {
                imgElement.src = getCharacterImageUrl(characterId, character);
                imgElement.alt = character.name;
                
                // 处理图片加载错误
                imgElement.onerror = function() {
                    console.error(`角色图片加载失败: ${imgElement.src}`);
                    this.src = '/static/images/default.svg';
                };
                
                // 图片加载完成后淡入
                imgElement.onload = function() {
                    element.style.opacity = '1';
                    console.log(`角色已平滑切换: ${character.name} 在 ${position} 位置`);
                    
                    // 添加呼吸效果
                    this.classList.add('character-breathing');
                };
            }
            
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
    Object.values(characterElements).forEach(element => {
        if (element) {
            element.style.opacity = '0';
            const img = element.querySelector('.character-img');
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