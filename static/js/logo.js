// Logo显示控制 - 控制页面上的logo.svg图片显示
async function initializeLogo() {
    try {
        // 获取设置
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // 检查是否显示Logo
        const showLogo = shouldShowLogo(settings);
        
        // 应用Logo显示设置
        applyLogoDisplay(showLogo);
        
    } catch (error) {
        console.error('获取Logo设置失败:', error);
        // 出现错误时，默认显示Logo
        applyLogoDisplay(true);
    }
}

// 判断是否应该显示Logo
function shouldShowLogo(settings) {
    // 默认显示Logo，只有明确设置为false才隐藏
    return settings.ui?.show_logo !== false;
}

// 应用Logo显示设置
function applyLogoDisplay(showLogo) {
    const splash = document.getElementById('logoSplash');
    const homePage = document.getElementById('homePage');
    
    if (splash && homePage) {
        if (showLogo) {
            // 显示Logo动画
            splash.style.display = 'flex';  // 改为flex以居中显示
            homePage.style.display = 'none';
            setTimeout(() => {
                splash.style.display = 'none';
                homePage.style.display = '';
            }, 1000);
        } else {
            // 直接显示主页，隐藏Logo
            splash.style.display = 'none';
            homePage.style.display = '';
        }
    }
    
    // 同时控制控制台Logo显示
    if (showLogo) {
        console.log(`
 ██████╗ █████╗ ██████╗ ███╗   ███╗
██╔════╝██╔══██╗██╔══██╗████╗ ████║
██║     ███████║██████╔╝██╔████╔██║
██║     ██╔══██║██╔══██╗██║╚██╔╝██║
╚██████╗██║  ██║██████╔╝██║ ╚═╝ ██║
 ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝`);
    }
}

// 监听设置面板中的Logo显示切换
document.addEventListener('DOMContentLoaded', function() {
    const showLogoToggle = document.getElementById('showLogoToggle');
    if (showLogoToggle) {
        // 获取当前设置并初始化切换按钮状态
        fetch('/api/settings')
            .then(response => response.json())
            .then(settings => {
                const showLogo = shouldShowLogo(settings);
                showLogoToggle.checked = showLogo;
            })
            .catch(error => {
                console.error('获取Logo设置失败:', error);
                // 默认显示Logo
                showLogoToggle.checked = true;
            });
        
        // 监听切换事件
        showLogoToggle.addEventListener('change', function() {
            const showLogo = this.checked;
            
            // 更新设置
            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ui: {
                        show_logo: showLogo
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Logo显示设置已更新');
                    // 重新应用Logo显示设置
                    applyLogoDisplay(showLogo);
                } else {
                    console.error('更新Logo显示设置失败:', data.error);
                    // 恢复切换按钮状态
                    this.checked = !showLogo;
                }
            })
            .catch(error => {
                console.error('更新Logo显示设置失败:', error);
                // 恢复切换按钮状态
                this.checked = !showLogo;
            });
        });
    }
});

// 页面加载时初始化Logo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeLogo);
} else {
    initializeLogo();
}