/**
 * K线图表处理类
 * 专门处理K线图的绘制和交互功能
 */
class KLineChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error(`Canvas element with id '${canvasId}' not found`);
            return;
        }
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
        this.data = null;
        this.config = this.getDefaultConfig();
    }
    
    /**
     * 检查Chart.js是否可用
     */
    isChartAvailable() {
        if (typeof Chart === 'undefined') {
            console.error('Chart.js is not loaded');
            return false;
        }
        return true;
    }

    /**
     * 获取默认图表配置
     */
    getDefaultConfig() {
        const config = {
            type: 'line',
            data: {
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'line',
                            font: {
                                size: 12,
                                weight: '600'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            title: function(context) {
                                const timestamp = context[0].parsed.x;
                                const date = new Date(timestamp);
                                return date.toLocaleString('zh-CN', {
                                    year: 'numeric',
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                });
                            },
                            label: function(context) {
                                const datasetLabel = context.dataset.label || '';
                                const value = context.parsed.y;
                                return `${datasetLabel}: ${value.toFixed(6)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: '时间',
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            lineWidth: 1
                        },
                        ticks: {
                            callback: function(value, index, ticks) {
                                // 将时间戳转换为可读格式
                                const date = new Date(value);
                                return date.toLocaleDateString('zh-CN', {
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                });
                            },
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '价格',
                            font: {
                                size: 14,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            lineWidth: 1
                        },
                        ticks: {
                            callback: function(value) {
                                return value.toFixed(6);
                            }
                        }
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        };

        // 如果zoom插件可用，添加缩放功能
        if (typeof Chart !== 'undefined' && Chart.register && window.chartjsPluginZoom) {
            try {
                Chart.register(window.chartjsPluginZoom.default || window.chartjsPluginZoom);
                config.options.plugins.zoom = {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                };
            } catch (error) {
                console.warn('缩放插件注册失败:', error);
            }
        }

        return config;
    }

    /**
     * 创建K线数据集
     */
    createCandlestickDataset(klineData, label, color) {
        return {
            label: label,
            data: klineData.map(item => ({
                x: item.timestamp,
                o: item.open,
                h: item.high,
                l: item.low,
                c: item.close
            })),
            backgroundColor: color.background,
            borderColor: color.border,
            borderWidth: 1
        };
    }

    /**
     * 创建折线数据集
     */
    createLineDataset(klineData, label, color, field = 'close') {
        return {
            label: label,
            data: klineData.map(item => ({
                x: item.timestamp,
                y: item[field]
            })),
            borderColor: color.border,
            backgroundColor: color.background,
            borderWidth: 2,
            fill: false,
            tension: 0.1,
            pointRadius: 0,
            pointHoverRadius: 4,
            pointBackgroundColor: color.border,
            pointBorderColor: '#fff',
            pointBorderWidth: 2
        };
    }

    /**
     * 初始化图表
     */
    initChart(realData, predData, chartType = 'line') {
        if (!this.isChartAvailable() || !this.canvas) {
            console.error('Cannot initialize chart: dependencies missing');
            return;
        }
        
        this.data = { real: realData, pred: predData };
        
        const datasets = [];
        
        if (chartType === 'candlestick') {
            // K线图模式（简化为折线图，因为Chart.js原生不支持K线图）
            datasets.push(this.createLineDataset(
                realData, 
                '真实价格', 
                {
                    border: 'rgba(40, 167, 69, 1)',
                    background: 'rgba(40, 167, 69, 0.1)'
                }
            ));
            
            datasets.push(this.createLineDataset(
                predData, 
                '预测价格', 
                {
                    border: 'rgba(220, 53, 69, 1)',
                    background: 'rgba(220, 53, 69, 0.1)'
                }
            ));
        } else if (chartType === 'line') {
            // 折线图模式
            datasets.push(this.createLineDataset(
                realData, 
                '真实价格', 
                {
                    border: 'rgba(40, 167, 69, 1)',
                    background: 'rgba(40, 167, 69, 0.1)'
                }
            ));
            
            datasets.push(this.createLineDataset(
                predData, 
                '预测价格', 
                {
                    border: 'rgba(220, 53, 69, 1)',
                    background: 'rgba(220, 53, 69, 0.1)'
                }
            ));
        } else if (chartType === 'both') {
            // 同时显示K线和折线
            datasets.push(this.createLineDataset(
                realData, 
                '真实价格', 
                {
                    border: 'rgba(40, 167, 69, 1)',
                    background: 'rgba(40, 167, 69, 0.1)'
                }
            ));
            
            datasets.push(this.createLineDataset(
                predData, 
                '预测价格', 
                {
                    border: 'rgba(220, 53, 69, 1)',
                    background: 'rgba(220, 53, 69, 0.1)'
                }
            ));
        }

        this.config.data.datasets = datasets;

        // 销毁现有图表
        if (this.chart) {
            this.chart.destroy();
        }

        try {
            // 创建新图表
            this.chart = new Chart(this.ctx, this.config);
            console.log('Chart initialized successfully');
        } catch (error) {
            console.error('Failed to create chart:', error);
        }
    }

    /**
     * 更新图表数据
     */
    updateChart(realData, predData, chartType = 'line') {
        if (!this.chart) {
            this.initChart(realData, predData, chartType);
            return;
        }

        const datasets = [];
        
        if (chartType === 'line' || chartType === 'both') {
            datasets.push(this.createLineDataset(
                realData, 
                '真实价格', 
                {
                    border: 'rgba(40, 167, 69, 1)',
                    background: 'rgba(40, 167, 69, 0.1)'
                }
            ));
            
            datasets.push(this.createLineDataset(
                predData, 
                '预测价格', 
                {
                    border: 'rgba(220, 53, 69, 1)',
                    background: 'rgba(220, 53, 69, 0.1)'
                }
            ));
        }

        this.chart.data.datasets = datasets;
        this.chart.update('none'); // 不使用动画更新
    }

    /**
     * 应用时间范围过滤
     */
    applyTimeRange(timeRange) {
        if (!this.data || !this.chart) return;

        const now = new Date();
        let startTime;

        switch (timeRange) {
            case '24h':
                startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                break;
            case '3d':
                startTime = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
                break;
            case '7d':
                startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30d':
                startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
            case 'all':
            default:
                startTime = null;
                break;
        }

        try {
            if (startTime) {
                this.chart.options.scales.x.min = startTime.getTime();
                this.chart.options.scales.x.max = now.getTime();
            } else {
                delete this.chart.options.scales.x.min;
                delete this.chart.options.scales.x.max;
            }

            this.chart.update('none');
        } catch (error) {
            console.error('Error applying time range:', error);
        }
    }

    /**
     * 重置缩放
     */
    resetZoom() {
        if (this.chart) {
            this.chart.resetZoom();
        }
    }

    /**
     * 获取当前可见时间范围的数据
     */
    getVisibleRangeData() {
        if (!this.chart || !this.data) return null;

        const scales = this.chart.scales;
        const minTime = scales.x.min || scales.x.options.min;
        const maxTime = scales.x.max || scales.x.options.max;

        if (!minTime || !maxTime) {
            return {
                real: this.data.real,
                pred: this.data.pred
            };
        }

        const realFiltered = this.data.real.filter(item => 
            item.timestamp >= minTime && item.timestamp <= maxTime
        );
        
        const predFiltered = this.data.pred.filter(item => 
            item.timestamp >= minTime && item.timestamp <= maxTime
        );

        return {
            real: realFiltered,
            pred: predFiltered
        };
    }

    /**
     * 销毁图表
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}

/**
 * 误差图表处理类
 */
class ErrorChart {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.chart = null;
    }

    /**
     * 初始化误差图表
     */
    initChart(errorData, displayType = 'absolute') {
        const config = {
            type: 'line',
            data: {
                datasets: [{
                    label: displayType === 'absolute' ? '绝对误差' : '百分比误差(%)',
                    data: errorData.map(item => ({
                        x: item.timestamp,
                        y: displayType === 'absolute' ? item.error : item.error_pct
                    })),
                    borderColor: 'rgba(111, 66, 193, 1)',
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 1,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x'
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        callbacks: {
                            title: function(context) {
                                const timestamp = context[0].parsed.x;
                                const date = new Date(timestamp);
                                return date.toLocaleString('zh-CN');
                            },
                            label: function(context) {
                                const value = context.parsed.y;
                                const suffix = displayType === 'absolute' ? '' : '%';
                                return `误差: ${value.toFixed(4)}${suffix}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        title: {
                            display: true,
                            text: '时间'
                        },
                        ticks: {
                            callback: function(value, index, ticks) {
                                const date = new Date(value);
                                return date.toLocaleDateString('zh-CN', {
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit'
                                });
                            },
                            maxTicksLimit: 8
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: displayType === 'absolute' ? '误差值' : '误差百分比(%)'
                        },
                        grid: {
                            color: function(context) {
                                if (context.tick.value === 0) {
                                    return 'rgba(220, 53, 69, 0.8)';
                                }
                                return 'rgba(0, 0, 0, 0.1)';
                            },
                            lineWidth: function(context) {
                                return context.tick.value === 0 ? 2 : 1;
                            }
                        }
                    }
                }
            }
        };

        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(this.ctx, config);
    }

    /**
     * 更新误差图表
     */
    updateChart(errorData, displayType = 'absolute') {
        if (!this.chart) {
            this.initChart(errorData, displayType);
            return;
        }

        this.chart.data.datasets[0].data = errorData.map(item => ({
            x: item.timestamp,
            y: displayType === 'absolute' ? item.error : item.error_pct
        }));

        this.chart.data.datasets[0].label = displayType === 'absolute' ? '绝对误差' : '百分比误差(%)';
        this.chart.options.scales.y.title.text = displayType === 'absolute' ? '误差值' : '误差百分比(%)';

        this.chart.update('none');
    }

    /**
     * 重置缩放
     */
    resetZoom() {
        if (this.chart) {
            this.chart.resetZoom();
        }
    }

    /**
     * 销毁图表
     */
    destroy() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }
}