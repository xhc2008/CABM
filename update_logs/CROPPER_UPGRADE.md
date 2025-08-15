# 头像裁剪功能升级说明

## 改进内容

### 1. 替换自制裁剪器为 Cropper.js
- **之前**: 使用自制的Canvas裁剪功能，功能有限，不支持长方形图片
- **现在**: 集成专业的 Cropper.js 库，功能强大，用户体验更好

### 2. 新功能特性
- ✅ 支持任意比例的图片（长方形、正方形都可以）
- ✅ 智能自适应图片尺寸
- ✅ 拖拽移动裁剪区域
- ✅ 鼠标滚轮缩放裁剪区域
- ✅ 高质量图片输出（200x200像素）
- ✅ 实时预览裁剪效果
- ✅ 响应式设计，支持移动端

### 3. 技术改进
- 使用 CDN 引入 Cropper.js (v1.6.1)
- 优化了模态框布局和样式
- 添加了科幻主题的自定义样式
- 改进了错误处理和用户反馈

## 文件修改清单

### HTML 模板 (templates/custom_character.html)
- 引入 Cropper.js CSS 和 JS 文件
- 更新裁剪模态框的HTML结构
- 替换 Canvas 元素为 img 元素

### JavaScript (static/js/custom_character.js)
- 移除自制的裁剪相关方法：
  - `initCropCanvas()`
  - `drawCropArea()`
  - `bindCropEvents()`
- 新增 Cropper.js 集成方法：
  - `initCropper()` - 初始化裁剪器
  - 优化 `confirmCrop()` - 使用 Cropper.js API
  - 优化 `hideCropModal()` - 正确销毁实例

### CSS 样式 (static/css/style.css)
- 添加 Cropper.js 自定义主题样式
- 优化头像预览样式
- 改进心情表格的科幻主题样式
- 添加响应式设计支持

## 使用方法

1. 点击"选择文件"上传头像图片
2. 图片上传后会显示预览和"裁剪头像"按钮
3. 点击"裁剪头像"打开裁剪器
4. 在裁剪器中：
   - 拖拽移动裁剪区域
   - 使用鼠标滚轮缩放
   - 拖拽角落调整大小
5. 点击"确认裁剪"完成裁剪
6. 裁剪后的图片会自动更新预览

## 测试

创建了 `test_cropper.html` 文件用于独立测试 Cropper.js 功能。
可以直接在浏览器中打开此文件测试裁剪功能是否正常工作。

## 兼容性

- 现代浏览器 (Chrome, Firefox, Safari, Edge)
- 移动端浏览器
- 支持触摸操作

## 注意事项

- Cropper.js 通过 CDN 加载，需要网络连接
- 如需离线使用，可下载 Cropper.js 文件到本地
- 裁剪输出固定为 200x200 像素的正方形图片
- 支持 PNG、JPG、WebP 等常见图片格式