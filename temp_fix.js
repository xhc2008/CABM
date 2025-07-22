// 修改第281行
const line281 = '                            await new Promise(resolve => setTimeout(resolve, 1));';

// 修改第302行
const line302 = '                            await new Promise(resolve => setTimeout(resolve, 1));';

// 修改第336行
const line336 = '                await new Promise(resolve => setTimeout(resolve, 1));';

const fs = require('fs');
const path = require('path');

// 读取文件
const filePath = path.join(__dirname, 'static', 'js', 'stream_handler.js');
let content = fs.readFileSync(filePath, 'utf8').split('\n');

// 替换行
content[280] = line281;
content[301] = line302;
content[335] = line336;

// 写回文件
fs.writeFileSync(filePath, content.join('\n'), 'utf8');

console.log('文件已成功修改');