/**
 * 主要JavaScript功能
 * 处理数据加载、图表初始化、用户交互等
 */

class WebVisualization {
    constructor() {
        this.data = null;
        this.priceChart = null;
        this.errorChart = null;
        this.currentTimeRange = '7d';
        this.currentChartType = 'line';
        this.currentErrorDisplay = 'absolute';
        
        this.init();
    }

    /**
     * 初始化应用
     */
    async init() {
        this.initEventListeners();
        this.showLoading();
        
        try {
            await this.loadData();
            this.initCharts();
            this.updateStatistics();
            this.updateLastUpdateTime();
        } catch (error) {
            console.error('初始化失败:', error);
            this.showError('数据加载失败，请检查数据文件是否存在');
        }
    }

    /**
     * 初始化事件监听器
     */
    initEventListeners() {
        // 时间范围选择
        document.getElementById('timeRange').addEventListener('change', (e) => {
            this.currentTimeRange = e.target.value;
            this.applyTimeRange();
            this.updateRangeStatistics();
        });

        // 图表类型选择
        document.getElementById('chartType').addEventListener('change', (e) => {
            this.currentChartType = e.target.value;
            this.updateChartType();
        });

        // 误差显示选择
        document.getElementById('errorDisplay').addEventListener('change', (e) => {
            this.currentErrorDisplay = e.target.value;
            this.updateErrorDisplay();
        });

        // 重置缩放按钮
        document.getElementById('resetZoom').addEventListener('click', () => {
            this.resetZoom();
        });

        // 刷新数据按钮
        document.getElementById('refreshData').addEventListener('click', () => {
            this.refreshData();
        });
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const loadingHtml = '<div class="loading">加载数据中...</div>';
        document.getElementById('dataOverview').innerHTML = loadingHtml;
        document.getElementById('performanceMetrics').innerHTML = loadingHtml;
    }

    /**
     * 显示错误信息
     */
    showError(message) {
        const errorHtml = `<div style="color: #dc3545; text-align: center; padding: 20px;">${message}</div>`;
        document.getElementById('dataOverview').innerHTML = errorHtml;
        document.getElementById('performanceMetrics').innerHTML = errorHtml;
    }

    /**
     * 加载数据
     */
    async loadData() {
        try {
            // 首先尝试加载简化数据
            const response = await fetch('data/kline_simplified_data.json');
            if (!response.ok) {
                // 如果简化数据不存在，尝试加载完整数据
                const fullResponse = await fetch('data/kline_comparison_data.json');
                if (!fullResponse.ok) {
                    throw new Error('无法加载数据文件');
                }
                this.data = await fullResponse.json();
            } else {
                this.data = await response.json();
            }
            
            console.log('数据加载成功:', this.data.metadata);
        } catch (error) {
            console.error('数据加载失败:', error);
            throw error;
        }
    }

    /**
     * 初始化图表
     */
    initCharts() {
        try {
            // 初始化价格图表
            this.priceChart = new KLineChart('priceChart');
            if (this.priceChart && this.data.real_kline && this.data.predicted_kline) {
                this.priceChart.initChart(
                    this.data.real_kline,
                    this.data.predicted_kline,
                    this.currentChartType
                );
            }

            // 初始化误差图表
            if (this.data.errors) {
                this.errorChart = new ErrorChart('errorChart');
                if (this.errorChart) {
                    this.errorChart.initChart(this.data.errors, this.currentErrorDisplay);
                }
            }

            // 应用默认时间范围
            this.applyTimeRange();
        } catch (error) {
            console.error('图表初始化失败:', error);
            this.showError('图表初始化失败: ' + error.message);
        }
    }

    /**
     * 应用时间范围过滤
     */
    applyTimeRange() {
        if (this.priceChart) {
            this.priceChart.applyTimeRange(this.currentTimeRange);
        }
        
        this.updateRangeStatistics();
    }

    /**
     * 更新图表类型
     */
    updateChartType() {
        if (this.priceChart && this.data) {
            this.priceChart.updateChart(
                this.data.real_kline,
                this.data.predicted_kline,
                this.currentChartType
            );
        }
    }

    /**
     * 更新误差显示类型
     */
    updateErrorDisplay() {
        const errorContainer = document.getElementById('errorContainer');
        
        if (this.currentErrorDisplay === 'none') {
            errorContainer.classList.add('hidden');
        } else {
            errorContainer.classList.remove('hidden');
            if (this.errorChart && this.data.errors) {
                this.errorChart.updateChart(this.data.errors, this.currentErrorDisplay);
            }
        }
    }

    /**
     * 重置缩放
     */
    resetZoom() {
        if (this.priceChart) {
            this.priceChart.resetZoom();
        }
        
        if (this.errorChart) {
            this.errorChart.resetZoom();
        }
        
        this.updateRangeStatistics();
    }

    /**
     * 刷新数据
     */
    async refreshData() {
        this.showLoading();
        
        try {
            await this.loadData();
            
            // 重新初始化图表
            if (this.priceChart) {
                this.priceChart.updateChart(
                    this.data.real_kline,
                    this.data.predicted_kline,
                    this.currentChartType
                );
            }
            
            if (this.errorChart && this.data.errors) {
                this.errorChart.updateChart(this.data.errors, this.currentErrorDisplay);
            }
            
            this.updateStatistics();
            this.updateLastUpdateTime();
            this.applyTimeRange();
            
        } catch (error) {
            console.error('数据刷新失败:', error);
            this.showError('数据刷新失败');
        }
    }

    /**
     * 更新统计信息
     */
    updateStatistics() {
        if (!this.data) return;

        // 数据概览
        const dataOverview = document.getElementById('dataOverview');
        dataOverview.innerHTML = `
            <p><strong>数据生成时间:</strong> ${new Date(this.data.metadata.generated_at).toLocaleString('zh-CN')}</p>
            <p><strong>数据周期:</strong> ${this.data.metadata.data_period_days} 天</p>
            <p><strong>总记录数:</strong> <span class="stat-value">${this.data.metadata.total_records}</span></p>
            <p><strong>总预测数:</strong> <span class="stat-value">${this.data.metadata.total_predictions}</span></p>
            <p><strong>序列长度:</strong> ${this.data.metadata.sequence_length}</p>
            <p><strong>目标特征:</strong> ${this.data.metadata.target_column}</p>
        `;

        // 性能指标
        if (this.data.statistics) {
            const stats = this.data.statistics;
            const performanceMetrics = document.getElementById('performanceMetrics');
            performanceMetrics.innerHTML = `
                <p><strong>平均绝对误差 (MAE):</strong> <span class="stat-value">${stats.mae.toFixed(6)}</span></p>
                <p><strong>均方根误差 (RMSE):</strong> <span class="stat-value">${stats.rmse.toFixed(6)}</span></p>
                <p><strong>平均绝对百分比误差 (MAPE):</strong> <span class="stat-value ${stats.mape > 10 ? 'stat-negative' : 'stat-positive'}">${stats.mape.toFixed(2)}%</span></p>
                <p><strong>方向预测准确率:</strong> <span class="stat-value ${stats.direction_accuracy > 50 ? 'stat-positive' : 'stat-negative'}">${stats.direction_accuracy.toFixed(2)}%</span></p>
                <p><strong>平均误差:</strong> <span class="stat-value ${stats.mean_error > 0 ? 'stat-positive' : 'stat-negative'}">${stats.mean_error.toFixed(6)}</span></p>
                <p><strong>误差标准差:</strong> <span class="stat-value">${stats.std_error.toFixed(6)}</span></p>
            `;
        }

        // 误差分布
        if (this.data.statistics) {
            const stats = this.data.statistics;
            const errorDistribution = document.getElementById('errorDistribution');
            errorDistribution.innerHTML = `
                <p><strong>最小误差:</strong> <span class="stat-value stat-positive">${stats.min_error.toFixed(6)}</span></p>
                <p><strong>最大误差:</strong> <span class="stat-value stat-negative">${stats.max_error.toFixed(6)}</span></p>
                <p><strong>误差中位数:</strong> <span class="stat-value">${stats.median_error.toFixed(6)}</span></p>
                <p><strong>误差范围:</strong> ${(stats.max_error - stats.min_error).toFixed(6)}</p>
            `;
        }
    }

    /**
     * 更新选定时间范围的统计信息
     */
    updateRangeStatistics() {
        if (!this.priceChart || !this.data) return;

        const visibleData = this.priceChart.getVisibleRangeData();
        if (!visibleData || !visibleData.real || !visibleData.pred) return;

        const realData = visibleData.real;
        const predData = visibleData.pred;

        if (realData.length === 0 || predData.length === 0) return;

        // 计算当前范围的统计信息
        const errors = [];
        const minLength = Math.min(realData.length, predData.length);

        for (let i = 0; i < minLength; i++) {
            if (realData[i] && predData[i] && realData[i].timestamp === predData[i].timestamp) {
                const error = predData[i].close - realData[i].close;
                const errorPct = (error / realData[i].close) * 100;
                errors.push({ error, errorPct });
            }
        }

        if (errors.length === 0) return;

        const absoluteErrors = errors.map(e => Math.abs(e.error));
        const absoluteErrorPcts = errors.map(e => Math.abs(e.errorPct));
        const errorValues = errors.map(e => e.error);

        const mae = absoluteErrors.reduce((a, b) => a + b, 0) / absoluteErrors.length;
        const mse = errorValues.reduce((a, b) => a + b * b, 0) / errorValues.length;
        const rmse = Math.sqrt(mse);
        const mape = absoluteErrorPcts.reduce((a, b) => a + b, 0) / absoluteErrorPcts.length;

        const rangeStatistics = document.getElementById('rangeStatistics');
        rangeStatistics.innerHTML = `
            <p><strong>当前范围数据点:</strong> <span class="stat-value">${errors.length}</span></p>
            <p><strong>时间范围:</strong> ${this.currentTimeRange}</p>
            <p><strong>MAE:</strong> <span class="stat-value">${mae.toFixed(6)}</span></p>
            <p><strong>RMSE:</strong> <span class="stat-value">${rmse.toFixed(6)}</span></p>
            <p><strong>MAPE:</strong> <span class="stat-value ${mape > 10 ? 'stat-negative' : 'stat-positive'}">${mape.toFixed(2)}%</span></p>
            <p><strong>最大绝对误差:</strong> <span class="stat-value">${Math.max(...absoluteErrors).toFixed(6)}</span></p>
        `;
    }

    /**
     * 更新最后更新时间
     */
    updateLastUpdateTime() {
        const lastUpdate = document.getElementById('lastUpdate');
        if (this.data && this.data.metadata) {
            const updateTime = new Date(this.data.metadata.generated_at);
            lastUpdate.textContent = updateTime.toLocaleString('zh-CN');
        } else {
            lastUpdate.textContent = new Date().toLocaleString('zh-CN');
        }
    }
}

// 检查依赖库是否加载成功
function checkDependencies() {
    const missing = [];
    if (typeof Chart === 'undefined') missing.push('Chart.js');
    if (typeof Hammer === 'undefined') missing.push('Hammer.js');
    
    if (missing.length > 0) {
        const errorMsg = `以下库未能加载: ${missing.join(', ')}\n请检查网络连接或使用本地文件。`;
        console.error(errorMsg);
        document.body.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column;">
                <h2 style="color: #dc3545;">依赖库加载失败</h2>
                <p>${errorMsg}</p>
                <button onclick="location.reload()" style="padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">重新加载</button>
            </div>
        `;
        return false;
    }
    return true;
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    // 等待一小段时间确保所有脚本都加载完成
    setTimeout(() => {
        if (checkDependencies()) {
            window.webViz = new WebVisualization();
        }
    }, 100);
});

// 全局错误处理
window.addEventListener('error', (e) => {
    console.error('全局错误:', e.error);
});

// 防止页面刷新时丢失状态
window.addEventListener('beforeunload', () => {
    // 可以在这里保存当前状态到localStorage
    if (window.webViz) {
        localStorage.setItem('webVizState', JSON.stringify({
            timeRange: window.webViz.currentTimeRange,
            chartType: window.webViz.currentChartType,
            errorDisplay: window.webViz.currentErrorDisplay
        }));
    }
});

// 页面加载时恢复状态
window.addEventListener('load', () => {
    const savedState = localStorage.getItem('webVizState');
    if (savedState && window.webViz) {
        try {
            const state = JSON.parse(savedState);
            
            // 恢复控件状态
            document.getElementById('timeRange').value = state.timeRange || '7d';
            document.getElementById('chartType').value = state.chartType || 'line';
            document.getElementById('errorDisplay').value = state.errorDisplay || 'absolute';
            
            // 应用状态
            window.webViz.currentTimeRange = state.timeRange || '7d';
            window.webViz.currentChartType = state.chartType || 'line';
            window.webViz.currentErrorDisplay = state.errorDisplay || 'absolute';
        } catch (e) {
            console.warn('恢复状态失败:', e);
        }
    }
});