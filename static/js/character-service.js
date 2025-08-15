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

/**
 * 调试说明：
 * - 要关闭呼吸动画，将 DEBUG_BREATHING_ENABLED 设置为 false
 * - 调整呼吸幅度，修改 DEBUG_BREATHING_INTENSITY 值：
 *   * 0.01 = 轻微呼吸 (scaleY: 1.0 ↔ 1.01)
 *   * 0.02 = 正常呼吸 (scaleY: 1.0 ↔ 1.02) [默认]
 *   * 0.03 = 明显呼吸 (scaleY: 1.0 ↔ 1.03)
 *   * 0.05 = 夸张呼吸 (scaleY: 1.0 ↔ 1.05)
 * - 呼吸动画会让角色在Y轴方向拉伸收缩，模拟呼吸效果
 * - 移动端会自动减少25%的幅度以优化性能
 * - 动画会自动遵循用户的"减少动画"偏好设置
 */

// 角色数据
let availableCharacters = [];
let currentCharacter = null;
let currentCharacterImages = [];
let isAnimating = false; // 防止动画冲突的标志

// 调试开关 - 呼吸动画控制
const DEBUG_BREATHING_ENABLED = true; // 设置为 false 可以关闭呼吸动画
const DEBUG_BREATHING_INTENSITY = 0.01; // 呼吸幅度：0.01=轻微, 0.02=正常, 0.03=明显, 0.05=夸张

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

// 直接设置当前角色（用于剧情模式）
export function setCurrentCharacter(character) {
    currentCharacter = character;
    console.log('角色服务 - 设置当前角色:', currentCharacter);
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
            // 将缩放应用到角色容器而不是图片，避免定位问题
            if (characterContainer) {
                characterContainer.style.transform = `translate(-50%, -50%) scale(${scaleValue})`;
                console.log(`缩放应用到角色容器: scale(${scaleValue})，避免定位偏移`);
            } else {
                // 如果找不到容器，则应用到图片（后备方案）
                characterImage.style.transform = `scale(${scaleValue}) scaleY(1)`;
                console.log(`缩放应用到图片元素: scale(${scaleValue}) (后备方案)`);
            }
            // 同时设置CSS变量，为后续的跳跃动画做准备
            characterImage.style.setProperty('--base-scale', scaleValue);
        } else if (characterImage) {
            console.log('使用默认缩放: 100%');
            // 将缩放应用到角色容器而不是图片，避免定位问题
            if (characterContainer) {
                characterContainer.style.transform = `translate(-50%, -50%) scale(1)`;
                console.log('使用默认缩放应用到角色容器: scale(1)');
            } else {
                // 如果找不到容器，则应用到图片（后备方案）
                characterImage.style.transform = 'scale(1) scaleY(1)';
                console.log('使用默认缩放应用到图片元素: scale(1) (后备方案)');
            }
            characterImage.style.setProperty('--base-scale', 1);
        }

        // 应用呼吸动画
        applyBreathingAnimation();
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
        image.onerror = function () {
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
                    // 将缩放应用到角色容器而不是图片，避免定位问题
                    const characterContainer = document.querySelector('.character-container');
                    if (characterContainer) {
                        characterContainer.style.transform = `translate(-50%, -50%) scale(${scaleValue})`;
                    } else {
                        // 如果找不到容器，则应用到图片（后备方案）
                        characterImage.style.transform = `scale(${scaleValue}) scaleY(1)`;
                    }
                    // 设置CSS变量，为后续的跳跃动画做准备
                    characterImage.style.setProperty('--base-scale', scaleValue);
                } else {
                    characterImage.style.setProperty('--base-scale', 1);
                }

                // 应用呼吸动画
                applyBreathingAnimation();
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

    // 防止动画冲突
    if (isAnimating) {
        console.log('动画进行中，跳过此次切换');
        return;
    }

    const targetImage = currentCharacterImages.find(img => img.number === imageNumber);

    if (targetImage) {
        console.log(`切换到图片 ${imageNumber}: ${targetImage.url}`);
        console.log(`角色缩放率: ${currentCharacter.scale_rate || 100}%, 跳跃动画将根据缩放率调整距离`);
        const characterImage = document.getElementById('characterImage');
        if (characterImage) {
            isAnimating = true;

            // 设置基础缩放率作为CSS变量
            const scaleValue = typeof currentCharacter.scale_rate !== 'undefined'
                ? currentCharacter.scale_rate / 100
                : 1;
            characterImage.style.setProperty('--base-scale', scaleValue);

            // 根据缩放率和屏幕尺寸计算合适的跳跃距离
            const isMobile = window.innerWidth <= 768;
            const baseJumpDistances = isMobile
                ? { d25: -8, d50: -12, d75: -3 }
                : { d25: -12, d50: -20, d75: -5 };

            // 根据缩放率调整跳跃距离，缩放率越小，跳跃距离应该越大（视觉上保持一致）
            const jumpScale = Math.max(0.5, 1 / scaleValue); // 最小0.5倍，避免过度夸张
            characterImage.style.setProperty('--jump-distance-25', `${baseJumpDistances.d25 * jumpScale}px`);
            characterImage.style.setProperty('--jump-distance-50', `${baseJumpDistances.d50 * jumpScale}px`);
            characterImage.style.setProperty('--jump-distance-75', `${baseJumpDistances.d75 * jumpScale}px`);

            console.log(`跳跃距离调整: 缩放率=${scaleValue.toFixed(2)}, 跳跃倍数=${jumpScale.toFixed(2)}, 最大跳跃=${(baseJumpDistances.d50 * jumpScale).toFixed(1)}px`);

            // 检查用户是否偏好减少动画
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

            // 添加跳跃动画效果（如果用户不偏好减少动画）
            if (!prefersReducedMotion) {
                // 暂时移除呼吸动画，避免冲突
                characterImage.classList.remove('character-breathing');
                characterImage.classList.add('character-jump');
            }

            // 在动画开始后稍微延迟切换图片，让跳跃效果更自然
            setTimeout(() => {
                characterImage.src = targetImage.url;
            }, 150);

            // 动画结束后移除动画类并恢复原始缩放
            // 根据屏幕尺寸和用户偏好调整动画时长
            const animationDuration = prefersReducedMotion ? 0 : (window.innerWidth <= 768 ? 400 : 500);
            setTimeout(() => {
                characterImage.classList.remove('character-jump');
                // 恢复角色容器的缩放，而不是图片的缩放
                const characterContainer = document.querySelector('.character-container');
                if (characterContainer) {
                    characterContainer.style.transform = `translate(-50%, -50%) scale(${scaleValue})`;
                } else {
                    // 如果找不到容器，则应用到图片（后备方案）
                    characterImage.style.transform = `scale(${scaleValue}) scaleY(1)`;
                }
                // 恢复呼吸动画
                applyBreathingAnimation();
                isAnimating = false;
            }, animationDuration);
        }
    } else {
        console.log(`未找到编号为 ${imageNumber} 的图片，使用默认图片`);
        const defaultImage = currentCharacterImages.find(img => img.number === 1);
        if (defaultImage) {
            const characterImage = document.getElementById('characterImage');
            if (characterImage) {
                isAnimating = true;

                // 设置基础缩放率作为CSS变量
                const scaleValue = typeof currentCharacter.scale_rate !== 'undefined'
                    ? currentCharacter.scale_rate / 100
                    : 1;
                characterImage.style.setProperty('--base-scale', scaleValue);

                // 根据缩放率和屏幕尺寸计算合适的跳跃距离
                const isMobile = window.innerWidth <= 768;
                const baseJumpDistances = isMobile
                    ? { d25: -8, d50: -12, d75: -3 }
                    : { d25: -12, d50: -20, d75: -5 };

                // 根据缩放率调整跳跃距离，缩放率越小，跳跃距离应该越大（视觉上保持一致）
                const jumpScale = Math.max(0.5, 1 / scaleValue); // 最小0.5倍，避免过度夸张
                characterImage.style.setProperty('--jump-distance-25', `${baseJumpDistances.d25 * jumpScale}px`);
                characterImage.style.setProperty('--jump-distance-50', `${baseJumpDistances.d50 * jumpScale}px`);
                characterImage.style.setProperty('--jump-distance-75', `${baseJumpDistances.d75 * jumpScale}px`);

                console.log(`跳跃距离调整: 缩放率=${scaleValue.toFixed(2)}, 跳跃倍数=${jumpScale.toFixed(2)}, 最大跳跃=${(baseJumpDistances.d50 * jumpScale).toFixed(1)}px`);

                // 检查用户是否偏好减少动画
                const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

                // 添加跳跃动画效果（如果用户不偏好减少动画）
                if (!prefersReducedMotion) {
                    // 暂时移除呼吸动画，避免冲突
                    characterImage.classList.remove('character-breathing');
                    characterImage.classList.add('character-jump');
                }

                setTimeout(() => {
                    characterImage.src = defaultImage.url;
                }, 150);

                // 动画结束后移除动画类并恢复原始缩放
                // 根据屏幕尺寸和用户偏好调整动画时长
                const animationDuration = prefersReducedMotion ? 0 : (window.innerWidth <= 768 ? 400 : 500);
                setTimeout(() => {
                    characterImage.classList.remove('character-jump');
                    // 恢复角色容器的缩放，而不是图片的缩放
                    const characterContainer = document.querySelector('.character-container');
                    if (characterContainer) {
                        characterContainer.style.transform = `translate(-50%, -50%) scale(${scaleValue})`;
                    } else {
                        // 如果找不到容器，则应用到图片（后备方案）
                        characterImage.style.transform = `scale(${scaleValue}) scaleY(1)`;
                    }
                    // 恢复呼吸动画
                    applyBreathingAnimation();
                    isAnimating = false;
                }, animationDuration);
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

// 应用呼吸动画
function applyBreathingAnimation() {
    const characterImage = document.getElementById('characterImage');
    if (characterImage && DEBUG_BREATHING_ENABLED) {
        // 检查用户是否偏好减少动画
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (!prefersReducedMotion) {
            // 根据屏幕尺寸调整呼吸幅度
            const isMobile = window.innerWidth <= 768;
            const adjustedIntensity = isMobile ? DEBUG_BREATHING_INTENSITY * 0.75 : DEBUG_BREATHING_INTENSITY;
            const breathingScale = 1 + adjustedIntensity;

            // 设置呼吸幅度CSS变量
            characterImage.style.setProperty('--breathing-scale', breathingScale);

            characterImage.classList.add('character-breathing');
            console.log(`呼吸动画已启用 (${isMobile ? '移动端' : '桌面端'})，幅度: ${adjustedIntensity.toFixed(3)} (scaleY: 1.0 ↔ ${breathingScale.toFixed(3)})`);
        } else {
            console.log('用户偏好减少动画，跳过呼吸动画');
        }
    } else if (!DEBUG_BREATHING_ENABLED) {
        console.log('呼吸动画已通过调试开关禁用');
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
