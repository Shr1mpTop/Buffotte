const { spawn } = require('child_process');
const path = require('path');
const { crawlerTimeout } = require('../config/database');

// 爬虫刷新函数（改进版本，修复路径问题）
async function refreshItemFromCrawler(itemId, itemName) {
  return new Promise((resolve, reject) => {
    // 构建爬虫命令 - 使用单个饰品更新器
    const projectRoot = path.join(__dirname, '../..');
    const crawlerPath = path.join(projectRoot, 'crawler/single_item_updater.py');
    const args = [];
    
    if (itemId) {
      args.push('--item-id', String(itemId));
    } else if (itemName) {
      args.push('--item-name', itemName);
    } else {
      reject(new Error('必须提供物品ID或名称'));
      return;
    }
    
    console.log(`执行爬虫命令: conda run -n buffotte python ${crawlerPath} ${args.join(' ')}`);
    console.log(`工作目录: ${projectRoot}`);
    
    const crawlerProcess = spawn('conda', ['run', '-n', 'buffotte', 'python', crawlerPath, ...args], {
      cwd: projectRoot,
      env: {
        ...process.env,
        PYTHONPATH: projectRoot,
        PYTHONIOENCODING: 'utf-8'
      }
    });
    
    let output = '';
    let errorOutput = '';
    
    crawlerProcess.stdout.on('data', (data) => {
      const text = data.toString('utf8');
      output += text;
      console.log('爬虫输出:', text.trim());
    });
    
    crawlerProcess.stderr.on('data', (data) => {
      const text = data.toString('utf8');
      errorOutput += text;
      console.error('爬虫错误:', text.trim());
    });
    
    crawlerProcess.on('close', (code) => {
      if (code === 0) {
        console.log('爬虫更新成功:', output);
        resolve(output);
      } else {
        console.error('爬虫更新失败:', errorOutput);
        reject(new Error(`爬虫进程退出码: ${code}, 错误: ${errorOutput}`));
      }
    });
    
    crawlerProcess.on('error', (error) => {
      console.error('爬虫进程启动失败:', error);
      reject(new Error(`爬虫进程启动失败: ${error.message}`));
    });
    
    // 设置超时
    setTimeout(() => {
      crawlerProcess.kill();
      reject(new Error('爬虫更新超时'));
    }, crawlerTimeout);
  });
}

module.exports = {
  refreshItemFromCrawler
};