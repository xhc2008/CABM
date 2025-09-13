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

/**
 * 初始化多角色服务
 */
export function initMultiCharacterService() {
    // 获取角色立绘元素
    characterElements.left = document.querySelector('.character-left');
    characterElements.right = document.querySelector('.character-right');
    characterElements.center = document.querySelector('.character-center');
    
    // 如果元素不存在，创建它们
    if (!characterElements.center) {
        createCharacterElements();
    }
    
    console.log('多角色服务已初始化');
}

/**
 * 创建角色立绘元素
 */
function createCharacterElements() {
    const chatContainer = document.querySelector('.chat-container') || document.body;
    
    // 创建角色容器
    const characterContainer = document.createElement('div');
    characterContainer.className = 'character-container';
    characterContainer.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 10;
    `;
    
    // 创建左侧角色元素
    const leftCharacter = document.createElement('div');
    leftCharacter.className = 'character-left';
    leftCharacter.style.cssText = `
        position: absolute;
        left: 10%;
        bottom: 0;
        width: 300px;
        height: 600px;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: bottom;
        opacity: 0;
        transition: all 0.5s ease;
        transform: translateX(-50px);
    `;
    
    // 创建右侧角色元素
    const rightCharacter = document.createElement('div');
    rightCharacter.className = 'character-right';
    rightCharacter.style.cssText = `
        position: absolute;
        right: 10%;
        bottom: 0;
        width: 300px;
        height: 600px;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: bottom;
        opacity: 0;
        transition: all 0.5s ease;
        transform: translateX(50px);
    `;
    
    // 创建中央角色元素（单角色模式使用）
    const centerCharacter = document.createElement('div');
    centerCharacter.className = 'character-center';
    centerCharacter.style.cssText = `
        position: absolute;
        left: 50%;
        bottom: 0;
        width: 400px;
        height: 700px;
        background-size: contain;
        background-repeat: no-repeat;
        background-position: bottom;
        opacity: 0;
        transition: all 0.5s ease;
        transform: translateX(-50%);
    `;
    
    // 添加到容器
    characterContainer.appendChild(leftCharacter);
    characterContainer.appendChild(rightCharacter);
    characterContainer.appendChild(centerCharacter);
    chatContainer.appendChild(characterContainer);
    
    // 更新元素引用
    characterElements.left = leftCharacter;
    characterElements.right = rightCharacter;
    characterElements.center = centerCharacter;
}

/**
 * 切换到指定角色
 * @param {string} characterId - 角色ID
 * @param {string} characterName - 角色名称
 */
export function switchToCharacter(characterId, characterName) {
    console.log(`切换到角色: ${characterName} (${characterId})`);
    
    // 获取角色配置
    fetch(`/api/characters/${characterId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const character = data.character;
                showCharacter(characterId, character, characterName);
            }
        })
        .catch(error => {
            console.error('获取角色配置失败:', error);
        });
}

/**
 * 显示角色立绘
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @param {string} characterName - 角色名称
 */
function showCharacter(characterId, character, characterName) {
    // 检查当前屏幕上的角色数量
    const activeCharacters = Object.values(currentCharacters).filter(char => char !== null);
    
    if (activeCharacters.length === 0) {
        // 没有角色，显示在中央
        showCharacterAt('center', characterId, character, characterName);
    } else if (activeCharacters.length === 1) {
        // 有一个角色，将其移到一侧，新角色显示在另一侧
        const existingPosition = Object.keys(currentCharacters).find(pos => currentCharacters[pos] !== null);
        
        if (existingPosition === 'center') {
            // 将中央角色移到左侧，新角色显示在右侧
            const existingCharacter = currentCharacters.center;
            moveCharacterFromTo('center', 'left', existingCharacter);
            showCharacterAt('right', characterId, character, characterName);
        } else {
            // 已经有左右角色，随机替换一个
            const targetPosition = Math.random() < 0.5 ? 'left' : 'right';
            showCharacterAt(targetPosition, characterId, character, characterName);
        }
    } else {
        // 有两个角色，随机替换一个
        const targetPosition = Math.random() < 0.5 ? 'left' : 'right';
        showCharacterAt(targetPosition, characterId, character, characterName);
    }
}

/**
 * 在指定位置显示角色
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @param {string} characterName - 角色名称
 */
function showCharacterAt(position, characterId, character, characterName) {
    const element = characterElements[position];
    if (!element) return;
    
    // 获取角色立绘URL
    const imageUrl = getCharacterImageUrl(characterId, character);
    
    // 更新角色状态
    currentCharacters[position] = {
        id: characterId,
        name: characterName,
        character: character
    };
    
    // 设置立绘
    element.style.backgroundImage = `url(${imageUrl})`;
    
    // 显示动画
    element.style.opacity = '1';
    element.style.transform = position === 'center' ? 'translateX(-50%)' : 
                             position === 'left' ? 'translateX(0)' : 'translateX(0)';
    
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
    toElement.style.backgroundImage = fromElement.style.backgroundImage;
    
    // 更新角色状态
    currentCharacters[toPosition] = characterData;
    currentCharacters[fromPosition] = null;
    
    // 隐藏原位置
    fromElement.style.opacity = '0';
    fromElement.style.backgroundImage = '';
    
    // 显示新位置
    toElement.style.opacity = '1';
    toElement.style.transform = toPosition === 'center' ? 'translateX(-50%)' : 
                               toPosition === 'left' ? 'translateX(0)' : 'translateX(0)';
    
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
export function showCharacterResponse(characterName) {
    console.log(`${characterName} 正在回复...`);
    
    // 可以在这里添加视觉指示，比如角色发光效果
    const speakingCharacter = findCharacterByName(characterName);
    if (speakingCharacter) {
        const element = characterElements[speakingCharacter.position];
        if (element) {
            element.style.filter = 'brightness(1.2) drop-shadow(0 0 20px rgba(255, 255, 255, 0.5))';
        }
    }
}

/**
 * 更新角色回复内容
 * @param {string} content - 回复内容
 */
export function updateCharacterResponse(content) {
    // 注意：文本内容的显示由主流处理器(streamProcessor)处理
    // 这里主要处理角色特定的视觉效果，如立绘高亮、对话框等
    
    // 找到当前说话的角色并添加视觉效果
    const speakingCharacter = findCurrentSpeakingCharacter();
    if (speakingCharacter) {
        const element = characterElements[speakingCharacter.position];
        if (element) {
            // 添加说话时的视觉效果
            element.style.filter = 'brightness(1.2) drop-shadow(0 0 20px rgba(255, 255, 255, 0.5))';
        }
    }
    
    console.log('角色回复视觉效果已更新:', content.substring(0, 50) + '...');
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
    Object.values(characterElements).forEach(element => {
        if (element) {
            element.style.filter = '';
        }
    });
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
 * 根据ID获取角色完整信息（从后端API获取）
 * @param {string} characterId - 角色ID
 * @returns {Promise<Object|null>} 角色完整信息
 */
export async function getCharacterById(characterId) {
    try {
        const response = await fetch(`/api/characters/${characterId}`);
        const data = await response.json();
        
        if (data.success) {
            return data.character;
        } else {
            console.error('获取角色信息失败:', data.error);
            return null;
        }
    } catch (error) {
        console.error('获取角色信息时发生错误:', error);
        return null;
    }
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

/**
 * 清除所有角色
 */
export function clearAllCharacters() {
    Object.values(characterElements).forEach(element => {
        if (element) {
            element.style.opacity = '0';
            element.style.backgroundImage = '';
            element.style.filter = '';
        }
    });
    
    currentCharacters = {
        left: null,
        right: null,
        center: null
    };
    
    console.log('已清除所有角色');
}

// 暴露给全局使用
window.switchToCharacter = switchToCharacter;
window.showCharacterResponse = showCharacterResponse;
window.updateCharacterResponse = updateCharacterResponse;
window.completeCharacterResponse = completeCharacterResponse;
window.getCharacterById = getCharacterById;
window.getCharacterBasicInfo = getCharacterBasicInfo;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initMultiCharacterService);