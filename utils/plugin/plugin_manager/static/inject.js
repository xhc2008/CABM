// 插件管理器注入脚本
(function() {
    // 等待DOM加载完成
    document.addEventListener('DOMContentLoaded', function() {
        // 检查是否在主页
        const homePage = document.getElementById('homePage');
        if (homePage) {
            // 查找按钮容器
            const buttonsContainer = homePage.querySelector('.home-buttons');
            if (buttonsContainer) {
                // 创建插件管理按钮
                const pluginButton = document.createElement('a');
                pluginButton.href = '/plugin-manager/plugins';
                pluginButton.className = 'btn secondary-btn';
                pluginButton.textContent = '插件管理';
                
                // 在退出按钮之前插入插件管理按钮
                const exitButton = document.getElementById('exitButton');
                if (exitButton) {
                    buttonsContainer.insertBefore(pluginButton, exitButton);
                } else {
                    buttonsContainer.appendChild(pluginButton);
                }
            }
        }
    });
})();