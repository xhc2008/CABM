// 角色管理服务模块
import { 
    characterName, 
    characterModal, 
    characterList, 
    currentMessage,
    loadingIndicator,
    errorMessage,
    errorContainer
} from './dom-elements.js';

// 角色数据
let availableCharacters = [];
let currentCharacter = null;
let currentCharacterImages = [];

// 显示加载指示器
function showLoading() {
    loadingIndicator.style.display = 'flex';
}

// 隐藏加载指示器
function hideLoading() {
    loadingIndicator.style.display = 'none';
}

// 显示错误信息
function showError(message) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
}

// 获取当前角色
export function getCurrentCharacter() {
    return currentCharacter;
}

// 获取可用角色列表
export function getAvailableCharacters() {
    return availableCharacters;
}

// 获取当前角色图片列表
export function getCurrentCharacterImages() {
    return currentCharacterImages;
}

// 加载角色数据
export async function loadCharacters() {
    try {
        showLoading();
        
        const response = await fetch('/api/characters');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        availableCharacters = data.available_characters;
        currentCharacter = data.current_character;
        
        console.log('当前角色信息:', currentCharacter);
        
        // 更新角色图片
        updateCharacterImage();
        
        // 更新当前消息
        if (currentCharacter && currentCharacter.welcome) {
            updateCurrentMessage('assistant', currentCharacter.welcome);
        } else {
            updateCurrentMessage('assistant', '欢迎使用CABM！我是您的AI助手，请输入消息开始对话。');
        }
        
    } catch (error) {
        console.error('加载角色数据失败:', error);
        showError(`加载角色数据失败: ${error.message}`);
        updateCurrentMessage('assistant', '欢迎使用CABM！我是您的AI助手，请输入消息开始对话。');
    } finally {
        hideLoading();
    }
}

// 更新角色图片
function updateCharacterImage() {
    const characterImage = document.getElementById('characterImage');
    const characterContainer = document.querySelector('.character-container');

    if (currentCharacter && characterImage) {
        loadCharacterImages(currentCharacter.id);

        if (characterContainer && typeof currentCharacter.calib !== 'undefined') {
            const baseTop = 50;
            const adjustedTop = baseTop + currentCharacter.calib;
            console.log(`角色位置调整: CALIB=${currentCharacter.calib}, 调整后位置=${adjustedTop}%`);
            characterContainer.style.top = `${adjustedTop}%`;
        } else if (characterContainer) {
            console.log('使用默认位置: 50%');
            characterContainer.style.top = '50%';
        }

        // 应用缩放率
        if (characterImage && typeof currentCharacter.scale_rate !== 'undefined') {
            const scaleValue = currentCharacter.scale_rate / 100; // 将百分比转换为小数
            console.log(`角色缩放调整: SCALE_RATE=${currentCharacter.scale_rate}%, 缩放值=${scaleValue}`);
            characterImage.style.transform = `scale(${scaleValue})`;
        } else if (characterImage) {
            console.log('使用默认缩放: 100%');
            characterImage.style.transform = 'scale(1)';
        }
    }
}

// 切换角色选择弹窗
export function toggleCharacterModal() {
    if (characterModal.style.display === 'flex') {
        characterModal.style.display = 'none';
    } else {
        characterModal.style.display = 'flex';
        renderCharacterList();
    }
}

// 渲染角色列表
function renderCharacterList() {
    characterList.innerHTML = '';
    
    availableCharacters.forEach(character => {
        const card = document.createElement('div');
        card.className = `character-card ${currentCharacter && character.id === currentCharacter.id ? 'active' : ''}`;
        card.dataset.characterId = character.id;

        const imageContainer = document.createElement('div');
        imageContainer.className = 'character-card-image';
        const image = document.createElement('img');
        // 优先使用avatar.png，如果不存在则使用第一张立绘
        const avatarUrl = character.image.endsWith('/')
            ? `${character.image}avatar.png`
            : `${character.image}/avatar.png`;
        const fallbackUrl = character.image.endsWith('/')
            ? `${character.image}1.png`
            : `${character.image}/1.png`;
        
        image.src = avatarUrl;
        image.alt = character.name;
        
        // 如果avatar.png加载失败，使用第一张立绘作为后备
        image.onerror = function() {
            this.src = fallbackUrl;
        };
        
        imageContainer.appendChild(image);

        const name = document.createElement('div');
        name.className = 'character-card-name';
        name.textContent = character.name;
        name.style.color = character.color;

        const description = document.createElement('div');
        description.className = 'character-card-description';
        description.textContent = character.description;

        card.appendChild(imageContainer);
        card.appendChild(name);
        card.appendChild(description);

        card.addEventListener('click', () => {
            selectCharacter(character.id);
        });

        characterList.appendChild(card);
    });
}

// 选择角色
export async function selectCharacter(characterId) {
    try {
        showLoading();
        
        const response = await fetch(`/api/characters/${characterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || '请求失败');
        }
        
        currentCharacter = data.character;
        console.log('切换后的角色信息:', currentCharacter);
        
        updateCharacterImage();
        renderCharacterList();
        
        if (currentCharacter.welcome) {
            updateCurrentMessage('assistant', currentCharacter.welcome);
        }
        
        // 隐藏选项按钮 - 需要从外部传入
        if (window.hideOptionButtons) {
            window.hideOptionButtons();
        }
        
        toggleCharacterModal();
        
    } catch (error) {
        console.error('选择角色失败:', error);
        showError(`选择角色失败: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// 加载角色图片列表
async function loadCharacterImages(characterId) {
    if (!characterId) {
        console.log('没有角色ID，无法加载图片');
        return;
    }

    try {
        console.log(`加载角色 ${characterId} 的图片列表`);

        const response = await fetch(`/api/characters/${characterId}/images`);
        const data = await response.json();

        if (data.success) {
            currentCharacterImages = data.images;
            console.log(`成功加载 ${currentCharacterImages.length} 张图片:`, currentCharacterImages);

            const characterImage = document.getElementById('characterImage');
            if (characterImage && data.default_image) {
                characterImage.src = data.default_image;
                console.log(`设置默认图片: ${data.default_image}`);
                // 应用缩放率
                if (typeof currentCharacter.scale_rate !== 'undefined') {
                    const scaleValue = currentCharacter.scale_rate / 100;
                    characterImage.style.transform = `scale(${scaleValue})`;
                }
            }
        } else {
            console.error('加载角色图片失败:', data.error);
            currentCharacterImages = [];
        }
    } catch (error) {
        console.error('加载角色图片时发生错误:', error);
        currentCharacterImages = [];
    }
}

// 切换角色图片
export function switchCharacterImage(imageNumber) {
    if (!currentCharacter) {
        console.log('没有当前角色，无法切换图片');
        return;
    }

    const targetImage = currentCharacterImages.find(img => img.number === imageNumber);

    if (targetImage) {
        console.log(`切换到图片 ${imageNumber}: ${targetImage.url}`);
        const characterImage = document.getElementById('characterImage');
        if (characterImage) {
            characterImage.src = targetImage.url;
            // 应用缩放率
            if (typeof currentCharacter.scale_rate !== 'undefined') {
                const scaleValue = currentCharacter.scale_rate / 100;
                characterImage.style.transform = `scale(${scaleValue})`;
            }
        }
    } else {
        console.log(`未找到编号为 ${imageNumber} 的图片，使用默认图片`);
        const defaultImage = currentCharacterImages.find(img => img.number === 1);
        if (defaultImage) {
            const characterImage = document.getElementById('characterImage');
            if (characterImage) {
                characterImage.src = defaultImage.url;
                // 应用缩放率
                if (typeof currentCharacter.scale_rate !== 'undefined') {
                    const scaleValue = currentCharacter.scale_rate / 100;
                    characterImage.style.transform = `scale(${scaleValue})`;
                }
            }
        } else {
            console.log('连默认图片都没有找到');
        }
    }
}

// 处理mood变化
export function handleMoodChange(moodNumber) {
    console.log('处理mood变化:', moodNumber);

    const imageNumber = parseInt(moodNumber);

    if (!isNaN(imageNumber) && imageNumber > 0) {
        switchCharacterImage(imageNumber);
    } else {
        console.log('mood不是有效数字，使用默认图片:', moodNumber);
        switchCharacterImage(1);
    }
}

// 更新当前消息 - 临时函数，应该从UI服务导入
function updateCurrentMessage(role, content) {
    if (role === 'user') {
        characterName.textContent = '你';
        characterName.style.color = '#90caf9';
    } else if (role === 'assistant') {
        if (currentCharacter) {
            characterName.textContent = currentCharacter.name;
            characterName.style.color = currentCharacter.color;
        } else {
            characterName.textContent = 'AI';
            characterName.style.color = '#ffeb3b';
        }
    } else if (role === 'system') {
        characterName.textContent = '系统';
        characterName.style.color = '#4caf50';
    }

    currentMessage.textContent = content;
}
