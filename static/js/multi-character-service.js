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

// 角色图片缓存 - 存储每个角色的图片列表
let characterImagesCache = new Map();

// 动画状态跟踪
let isAnimating = new Map(); // 跟踪每个位置的动画状态

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
    
    // 添加调试函数到全局
    window.debugCharacterElements = debugCharacterElements;
    
    console.log('多角色服务已初始化');
}

/**
 * 启用多角色模式
 */
export function enableMultiCharacterMode() {
    console.log('启用多角色模式');
    
    // 确保多角色容器存在
    if (!document.querySelector('.multi-character-container')) {
        createCharacterElements();
    }
    
    // 确保多角色容器可见
    const multiCharacterContainer = document.querySelector('.multi-character-container');
    if (multiCharacterContainer) {
        multiCharacterContainer.style.display = 'block';
        multiCharacterContainer.style.zIndex = '5'; // 确保在背景之上
        console.log('多角色容器已显示');
    }
    
    // 隐藏单角色模式的立绘
    hideSingleCharacterImage();
    
    console.log('多角色模式已启用');
}
function updateCharacterAtPosition(position, characterId, character, characterName) {
    const element = characterElements[position];
    if (!element) return;
    
    // 获取角色图片URL
    const imageUrl = getDefaultCharacterImageUrl(characterId, character);
    
    // 获取角色图片元素
    const characterImage = element.querySelector('.character-img');
    if (!characterImage) return;
    
    // 设置图片
    characterImage.src = imageUrl;
    characterImage.alt = characterName;
    
    // 应用角色配置
    applyCharacterConfig(element, character);
    
    console.log(`角色 ${characterName} 在 ${position} 位置已更新`);
}
/**
 * 禁用多角色模式（返回单角色模式）
 */
export function disableMultiCharacterMode() {
    console.log('禁用多角色模式');
    
    // 清除所有多角色立绘
    clearAllCharacters();
    
    // 隐藏多角色容器
    const multiCharacterContainer = document.querySelector('.multi-character-container');
    if (multiCharacterContainer) {
        multiCharacterContainer.style.display = 'none';
    }
    
    // 显示单角色模式的立绘
    showSingleCharacterImage();
    
    console.log('已返回单角色模式');
}

/**
 * 创建角色立绘元素
 */
function createCharacterElements() {
    const chatContainer = document.querySelector('.chat-container') || document.body;
    
    // 检查是否已存在多角色容器
    let characterContainer = document.querySelector('.multi-character-container');
    if (!characterContainer) {
        // 创建角色容器
        characterContainer = document.createElement('div');
        characterContainer.className = 'multi-character-container';
        characterContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 5; // 提高z-index确保在背景之上
            display: block; // 确保默认显示
        `;
        chatContainer.appendChild(characterContainer);
    }
    
    // 创建左侧角色元素
    if (!characterElements.left) {
        const leftCharacter = createCharacterElement('left', '15%', 'translateX(-50px)');
        characterContainer.appendChild(leftCharacter);
        characterElements.left = leftCharacter;
    }
    
    // 创建右侧角色元素
    if (!characterElements.right) {
        const rightCharacter = createCharacterElement('right', '85%', 'translateX(50px)');
        characterContainer.appendChild(rightCharacter);
        characterElements.right = rightCharacter;
    }
    
    // 创建中央角色元素
    if (!characterElements.center) {
        const centerCharacter = createCharacterElement('center', '50%', 'translateX(-50%)');
        characterContainer.appendChild(centerCharacter);
        characterElements.center = centerCharacter;
    }
    
    // 初始化动画状态
    isAnimating.set('left', false);
    isAnimating.set('right', false);
    isAnimating.set('center', false);
    
    console.log('多角色容器和立绘元素已创建');
}

/**
 * 创建单个角色元素
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {string} leftPosition - 左侧位置百分比
 * @param {string} initialTransform - 初始变换
 * @returns {HTMLElement} 角色元素
 */
function createCharacterElement(position, leftPosition, initialTransform) {
    const characterDiv = document.createElement('div');
    characterDiv.className = `character-${position}`;
    
    // 根据位置设置不同的定位方式，避免上下移动
    if (position === 'left') {
        characterDiv.style.cssText = `
            position: absolute;
            left: ${leftPosition};
            bottom: 0;
            width: 300px;
            height: 600px;
            opacity: 0;
            transition: opacity 0.5s ease, transform 0.5s ease;
            transform: translateX(-50px);
        `;
    } else if (position === 'right') {
        characterDiv.style.cssText = `
            position: absolute;
            right: ${leftPosition.replace('%', '')}%;
            bottom: 0;
            width: 300px;
            height: 600px;
            opacity: 0;
            transition: opacity 0.5s ease, transform 0.5s ease;
            transform: translateX(50px);
        `;
    } else { // center
        characterDiv.style.cssText = `
            position: absolute;
            left: 50%;
            bottom: 0;
            width: 400px;
            height: 700px;
            opacity: 0;
            transition: opacity 0.5s ease, transform 0.5s ease;
            transform: translateX(-50%);
        `;
    }
    
    // 创建角色图片容器
    const imageContainer = document.createElement('div');
    imageContainer.className = 'character-image-container';
    imageContainer.style.cssText = `
        position: relative;
        width: 100%;
        height: 100%;
    `;
    
    // 创建角色图片
    const characterImage = document.createElement('img');
    characterImage.className = 'character-img';
    characterImage.style.cssText = `
        width: 100%;
        height: 100%;
        object-fit: contain;
        object-position: bottom;
        display: block;
    `;
    
    imageContainer.appendChild(characterImage);
    characterDiv.appendChild(imageContainer);
    
    return characterDiv;
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
    
    // 检查是否已经有相同角色在不同位置
    const existingPosition = Object.keys(currentCharacters).find(
        pos => currentCharacters[pos] && currentCharacters[pos].id === characterId
    );
    
    if (existingPosition) {
        // 如果角色已经在屏幕上，只需更新该位置的图片
        console.log(`角色 ${characterName} 已在 ${existingPosition} 位置，更新图片`);
        updateCharacterAtPosition(existingPosition, characterId, character, characterName);
        return;
    }
    
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
            // 等待移动完成后再显示新角色
            setTimeout(() => {
                showCharacterAt('right', characterId, character, characterName);
            }, 100); // 添加短暂延迟确保移动完成
        } else {
            // 已经有左右角色，随机替换一个
            const targetPosition = existingPosition === 'left' ? 'right' : 'left';
            showCharacterAt(targetPosition, characterId, character, characterName);
        }
    } else {
        // 有两个角色，随机替换一个
        const positions = ['left', 'right'];
        const targetPosition = positions[Math.floor(Math.random() * positions.length)];
        showCharacterAt(targetPosition, characterId, character, characterName);
    }
}

function clearCharacterAtPosition(position) {
    const element = characterElements[position];
    if (!element) return;
    
    element.style.opacity = '0';
    
    const characterImage = element.querySelector('.character-img');
    if (characterImage) {
        characterImage.src = '';
    }
    
    currentCharacters[position] = null;
    console.log(`已清除 ${position} 位置的角色`);
}

/**
 * 在指定位置显示角色
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @param {string} characterName - 角色名称
 */
async function showCharacterAt(position, characterId, character, characterName) {
    // 检查是否已经在其他位置显示了这个角色
    for (const [pos, char] of Object.entries(currentCharacters)) {
        if (char && char.id === characterId && pos !== position) {
            console.log(`角色 ${characterName} 已在 ${pos} 位置显示，移动到 ${position}`);
            moveCharacterFromTo(pos, position, char);
            return;
        }
    }
    
    const element = characterElements[position];
    if (!element) return;
    
    // 如果该位置已经有其他角色，先清除
    if (currentCharacters[position]) {
        clearCharacterAtPosition(position);
    }
    
    // 更新角色状态
    currentCharacters[position] = {
        id: characterId,
        name: characterName,
        character: character
    };
    
    // 加载角色图片列表
    await loadCharacterImages(characterId);
    
    // 获取默认图片
    const imageUrl = getDefaultCharacterImageUrl(characterId, character);
    
    // 获取角色图片元素
    const characterImage = element.querySelector('.character-img');
    if (!characterImage) return;
    
    // 设置图片
    characterImage.src = imageUrl;
    characterImage.alt = characterName;
    
    // 应用角色配置（位置校准和缩放）
    applyCharacterConfig(element, character);
    
    // 显示动画
    element.style.opacity = '1';
    if (position === 'center') {
        element.style.transform = 'translateX(-50%)';
    } else {
        element.style.transform = 'translateX(0)';
    }
    
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
    
    // 获取源位置的图片
    const fromImage = fromElement.querySelector('.character-img');
    const toImage = toElement.querySelector('.character-img');
    
    if (fromImage && toImage) {
        // 复制图片到新位置
        toImage.src = fromImage.src;
        toImage.alt = fromImage.alt;
        
        // 复制角色配置到新位置
        applyCharacterConfig(toElement, characterData.character);
        
        // 更新角色状态
        currentCharacters[toPosition] = characterData;
        currentCharacters[fromPosition] = null;
        
        // 隐藏原位置 - 添加过渡效果
        fromElement.style.opacity = '0';
        setTimeout(() => {
            fromImage.src = '';
        }, 500); // 等待过渡完成后再清空图片
        
        // 显示新位置
        toElement.style.opacity = '1';
        if (toPosition === 'center') {
            toElement.style.transform = 'translateX(-50%)';
        } else {
            toElement.style.transform = 'translateX(0)';
        }
        
        console.log(`角色从 ${fromPosition} 移动到 ${toPosition}`);
    }
}

/**
 * 加载角色图片列表
 * @param {string} characterId - 角色ID
 * @returns {Promise<Array>} 图片列表
 */
async function loadCharacterImages(characterId) {
    if (!characterId) {
        console.log('没有角色ID，无法加载图片');
        return [];
    }
    
    // 检查缓存
    if (characterImagesCache.has(characterId)) {
        console.log(`从缓存获取角色图片列表: ${characterId}`);
        return characterImagesCache.get(characterId);
    }
    
    try {
        console.log(`加载角色 ${characterId} 的图片列表`);
        
        const response = await fetch(`/api/characters/${characterId}/images`);
        const data = await response.json();
        
        if (data.success) {
            characterImagesCache.set(characterId, data.images);
            console.log(`成功加载 ${data.images.length} 张图片:`, data.images);
            return data.images;
        } else {
            console.error('加载角色图片失败:', data.error);
            return [];
        }
    } catch (error) {
        console.error('加载角色图片时发生错误:', error);
        return [];
    }
}

/**
 * 获取默认角色立绘URL
 * @param {string} characterId - 角色ID
 * @param {Object} character - 角色配置
 * @returns {string} 立绘URL
 */
function getDefaultCharacterImageUrl(characterId, character) {
    // 优先使用角色配置中的立绘
    if (character.image_url) {
        return character.image_url;
    }
    
    // 检查缓存的图片列表
    const images = characterImagesCache.get(characterId);
    if (images && images.length > 0) {
        // 找到默认图片（通常是编号为1的图片）
        const defaultImage = images.find(img => img.number === 1) || images[0];
        return defaultImage.url;
    }
    
    // 使用默认立绘路径
    const defaultUrl = `/static/images/${characterId}/1.png`;
    console.log(`使用默认图片路径: ${defaultUrl}`);
    return defaultUrl;
}

/**
 * 应用角色配置（位置校准和缩放）
 * @param {HTMLElement} element - 角色元素
 * @param {Object} character - 角色配置
 */
function applyCharacterConfig(element, character) {
    if (!element || !character) return;
    
    const characterImage = element.querySelector('.character-img');
    if (!characterImage) return;
    
    // 应用位置校准 - 使用bottom定位避免上下移动
    if (typeof character.calib !== 'undefined') {
        const baseBottom = 0; // 基础位置是底部0px
        const adjustedBottom = baseBottom + character.calib * 5; // 将百分比转换为像素
        console.log(`角色位置调整: CALIB=${character.calib}, 调整后位置=${adjustedBottom}px`);
        element.style.bottom = `${adjustedBottom}px`;
    }
    
    // 应用缩放率 - 与单角色模式完全一致
    if (typeof character.scale_rate !== 'undefined') {
        const scaleValue = character.scale_rate / 100;
        console.log(`角色缩放调整: SCALE_RATE=${character.scale_rate}%, 缩放值=${scaleValue}`);
        
        // 应用缩放 - 保持底部对齐，避免上下移动
        const currentTransform = element.style.transform;
        const transformWithoutScale = currentTransform.replace(/scale\([^)]*\)/g, '').trim();
        
        // 根据位置设置基础变换
        let baseTransform;
        if (element.classList.contains('character-center')) {
            baseTransform = 'translateX(-50%)';
        } else {
            baseTransform = 'translateX(0)';
        }
        
        element.style.transform = `${baseTransform} ${transformWithoutScale} scale(${scaleValue})`;
        
        // 设置CSS变量，为后续的跳跃动画做准备
        characterImage.style.setProperty('--base-scale', scaleValue);
    } else {
        // 使用默认缩放
        const currentTransform = element.style.transform;
        const transformWithoutScale = currentTransform.replace(/scale\([^)]*\)/g, '').trim();
        
        // 根据位置设置基础变换
        let baseTransform;
        if (element.classList.contains('character-center')) {
            baseTransform = 'translateX(-50%)';
        } else {
            baseTransform = 'translateX(0)';
        }
        
        element.style.transform = `${baseTransform} ${transformWithoutScale} scale(1)`;
        characterImage.style.setProperty('--base-scale', 1);
    }
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

/**
 * 切换角色图片
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @param {number} imageNumber - 图片编号
 */
export async function switchCharacterImage(position, imageNumber) {
    const characterData = currentCharacters[position];
    if (!characterData) {
        console.log(`位置 ${position} 没有角色，无法切换图片`);
        return;
    }
    
    // 防止动画冲突
    if (isAnimating.get(position)) {
        console.log(`位置 ${position} 动画进行中，跳过此次切换`);
        return;
    }
    
    const element = characterElements[position];
    if (!element) return;
    
    const characterImage = element.querySelector('.character-img');
    if (!characterImage) return;
    
    // 获取角色图片列表
    const images = characterImagesCache.get(characterData.id);
    if (!images || images.length === 0) {
        console.log(`角色 ${characterData.id} 没有图片列表`);
        return;
    }
    
    const targetImage = images.find(img => img.number === imageNumber);
    if (!targetImage) {
        console.log(`找不到图片编号 ${imageNumber}`);
        return;
    }
    
    console.log(`切换到图片 ${imageNumber}: ${targetImage.url}`);
    
    // 设置动画状态
    isAnimating.set(position, true);
    
    // 设置基础缩放率作为CSS变量
    const scaleValue = typeof characterData.character.scale_rate !== 'undefined'
        ? characterData.character.scale_rate / 100
        : 1;
    characterImage.style.setProperty('--base-scale', scaleValue);
    
    // 添加跳跃动画
    characterImage.classList.add('character-jump');
    
    // 切换图片
    characterImage.src = targetImage.url;
    
    // 动画完成后清理
    setTimeout(() => {
        characterImage.classList.remove('character-jump');
        isAnimating.set(position, false);
    }, 600); // 动画持续时间
}

/**
 * 清除所有角色
 */
export function clearAllCharacters() {
    Object.values(characterElements).forEach(element => {
        if (element) {
            element.style.opacity = '0';
            element.style.filter = '';
            
            const characterImage = element.querySelector('.character-img');
            if (characterImage) {
                characterImage.src = '';
                characterImage.alt = '';
                characterImage.classList.remove('character-jump');
            }
        }
    });
    
    currentCharacters = {
        left: null,
        right: null,
        center: null
    };
    
    // 重置动画状态
    isAnimating.set('left', false);
    isAnimating.set('right', false);
    isAnimating.set('center', false);
    
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
        characterImagesCache.delete(characterId);
        console.log(`已清除角色缓存: ${characterId}`);
    } else {
        characterCache.clear();
        pendingRequests.clear();
        characterImagesCache.clear();
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
        cachedImages: characterImagesCache.size,
        cachedIds: Array.from(characterCache.keys())
    };
}

/**
 * 获取指定位置的角色信息
 * @param {string} position - 位置 ('left', 'right', 'center')
 * @returns {Object|null} 角色信息
 */
export function getCharacterAtPosition(position) {
    return currentCharacters[position] || null;
}

/**
 * 获取所有当前显示的角色
 * @returns {Array} 角色信息数组
 */
export function getAllCurrentCharacters() {
    return Object.values(currentCharacters).filter(char => char !== null);
}

/**
 * 隐藏单角色模式的立绘（在多角色模式下）
 */
export function hideSingleCharacterImage() {
    const singleCharacterContainer = document.querySelector('.character-container');
    if (singleCharacterContainer) {
        singleCharacterContainer.style.display = 'none';
        console.log('已隐藏单角色模式立绘');
    }
}

/**
 * 显示单角色模式的立绘（在单角色模式下）
 */
export function showSingleCharacterImage() {
    const singleCharacterContainer = document.querySelector('.character-container');
    if (singleCharacterContainer) {
        singleCharacterContainer.style.display = 'block';
        console.log('已显示单角色模式立绘');
    }
}
export function debugCharacterElements() {
    console.log('=== 多角色元素调试信息 ===');
    
    // 检查容器
    const container = document.querySelector('.multi-character-container');
    console.log('多角色容器:', container);
    if (container) {
        console.log('容器样式:', {
            display: container.style.display,
            opacity: container.style.opacity,
            zIndex: container.style.zIndex,
            visibility: container.style.visibility
        });
    }
    
    // 检查每个角色元素
    Object.entries(characterElements).forEach(([position, element]) => {
        console.log(`${position} 位置元素:`, element);
        if (element) {
            console.log(`${position} 样式:`, {
                display: element.style.display,
                opacity: element.style.opacity,
                transform: element.style.transform,
                left: element.style.left,
                right: element.style.right,
                bottom: element.style.bottom
            });
            
            const img = element.querySelector('.character-img');
            console.log(`${position} 图片:`, img);
            if (img) {
                console.log(`${position} 图片源:`, img.src);
            }
        }
    });
    
    console.log('当前角色状态:', currentCharacters);
    console.log('=== 调试信息结束 ===');
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
window.switchCharacterImage = switchCharacterImage;
window.getCharacterAtPosition = getCharacterAtPosition;
window.getAllCurrentCharacters = getAllCurrentCharacters;
window.hideSingleCharacterImage = hideSingleCharacterImage;
window.showSingleCharacterImage = showSingleCharacterImage;
window.enableMultiCharacterMode = enableMultiCharacterMode;
window.disableMultiCharacterMode = disableMultiCharacterMode;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', initMultiCharacterService);