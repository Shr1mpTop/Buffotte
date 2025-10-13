"""
Risk Control Officer Agent

Responsible for:
1. Validating strategy compliance with regulations and rules
2. Calculating risk exposure (position limits, VaR, etc.)
3. Setting risk thresholds (max drawdown, position limits, etc.)
4. Reviewing and approving/rejecting trading orders
"""
from typing import Dict, Any, List, Optional
from llm.agents.base_agent import BaseAgent
import numpy as np


class RiskControlAgent(BaseAgent):
    """风险控制专员Agent - 负责风险管理和合规审核"""
    
    def __init__(self, client, temperature: float = 0.2):
        """
        Initialize Risk Control Agent.
        
        Args:
            client: LLM client instance
            temperature: Sampling temperature (default 0.2 for conservative analysis)
        """
        super().__init__(
            name="RiskControlOfficer",
            role="风险控制专员",
            client=client,
            temperature=temperature
        )
        
        # Risk limits configuration
        self.risk_limits = {
            'max_position_size': 0.30,  # 最大单一仓位30%
            'max_drawdown': 0.15,  # 最大回撤15%
            'max_daily_loss': 0.05,  # 单日最大亏损5%
            'max_leverage': 2.0,  # 最大杠杆2倍
            'min_liquidity_ratio': 0.20,  # 最低流动性比例20%
            'max_correlation': 0.70,  # 最大相关性0.7
            'var_95_limit': 0.10,  # 95% VaR限制10%
        }
    
    def _build_system_instruction(self) -> str:
        """Build system instruction for risk control officer."""
        return """你是一名资深风险控制专员，负责审核交易策略的风险和合规性。

你的职责：
1. 校验交易策略是否符合风险管理规定和监管要求
2. 测算风险敞口（仓位集中度、行业敞口、VaR值等）
3. 设定和监控风险阈值（最大回撤、止损线、仓位限制）
4. 审核交易订单，拦截违规或高风险操作
5. 出具风险评估报告和合规检查报告

风险维度：
- 市场风险（价格波动、流动性风险）
- 信用风险（交易对手风险）
- 操作风险（系统故障、人为失误）
- 合规风险（违反监管规定）
- 流动性风险（无法及时平仓）

分析要求：
- 严格执行风险限额和合规要求
- 实时监控风险指标，及时预警
- 对高风险策略提出明确反对意见
- 给出风险缓释建议
- 保护资金安全是第一要务

风格：严谨、保守、原则性强、零容忍违规"""
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform risk control analysis and compliance check.
        
        Args:
            context: {
                'strategy': dict from StrategyManagerAgent,
                'historical_data': pd.DataFrame,
                'current_portfolio': dict (optional),
                'market_conditions': dict (optional)
            }
            
        Returns:
            {
                'report': str,
                'approval_status': str (APPROVED/REJECTED/CONDITIONAL),
                'risk_score': float (0-100, higher = riskier),
                'risk_level': str (LOW/MEDIUM/HIGH/CRITICAL),
                'compliance_check': dict,
                'risk_metrics': dict,
                'violations': list,
                'warnings': list,
                'recommendations': list,
                'key_findings': list
            }
        """
        print(f"\n🛡️ [{self.role}] 开始风险审核...")
        
        # Extract data
        strategy = context.get('strategy', {})
        df = context.get('historical_data')
        portfolio = context.get('current_portfolio', {})
        market_conditions = context.get('market_conditions', {})
        
        # Perform compliance check
        compliance_check = self._check_compliance(strategy, portfolio)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(strategy, df, portfolio)
        
        # Assess overall risk
        risk_score, risk_level = self._assess_overall_risk(
            strategy,
            risk_metrics,
            compliance_check
        )
        
        # Identify violations and warnings
        violations = self._identify_violations(compliance_check, risk_metrics)
        warnings = self._generate_warnings(risk_metrics, strategy)
        
        # Determine approval status
        approval_status = self._determine_approval_status(violations, risk_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            violations,
            warnings,
            risk_metrics,
            strategy
        )
        
        # Generate LLM analysis
        prompt = self._build_analysis_prompt(
            strategy,
            compliance_check,
            risk_metrics,
            risk_score,
            risk_level,
            approval_status,
            violations,
            warnings,
            recommendations
        )
        report = self._generate_response(prompt)
        
        # Extract key findings
        key_findings = self._extract_key_findings(
            approval_status,
            risk_level,
            violations,
            warnings
        )
        
        result = {
            'agent': self.name,
            'role': self.role,
            'report': report,
            'approval_status': approval_status,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'compliance_check': compliance_check,
            'risk_metrics': risk_metrics,
            'violations': violations,
            'warnings': warnings,
            'recommendations': recommendations,
            'key_findings': key_findings
        }
        
        print(f"✅ [{self.role}] 风控审核完成 - 状态: {approval_status}, 风险: {risk_level}")
        return result
    
    def _check_compliance(
        self,
        strategy: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance with risk limits and regulations."""
        checks = {
            'position_size': {'status': 'PASS', 'value': 0, 'limit': self.risk_limits['max_position_size']},
            'leverage': {'status': 'PASS', 'value': 1.0, 'limit': self.risk_limits['max_leverage']},
            'liquidity': {'status': 'PASS', 'value': 1.0, 'limit': self.risk_limits['min_liquidity_ratio']},
            'stop_loss': {'status': 'PASS', 'exists': False},
            'diversification': {'status': 'PASS', 'score': 0}
        }
        
        # Check position size
        position_size = strategy.get('position_size', 0)
        checks['position_size']['value'] = position_size
        if position_size > self.risk_limits['max_position_size']:
            checks['position_size']['status'] = 'FAIL'
        elif position_size > self.risk_limits['max_position_size'] * 0.8:
            checks['position_size']['status'] = 'WARNING'
        
        # Check stop loss exists
        stop_loss = strategy.get('stop_loss')
        if stop_loss is not None:
            checks['stop_loss']['exists'] = True
            entry_price = strategy.get('entry_price', 0)
            if entry_price > 0:
                stop_loss_pct = abs(entry_price - stop_loss) / entry_price
                checks['stop_loss']['value'] = stop_loss_pct
                if stop_loss_pct > 0.20:  # Stop loss > 20%
                    checks['stop_loss']['status'] = 'WARNING'
        else:
            checks['stop_loss']['status'] = 'WARNING'
        
        # Check leverage (simplified)
        current_leverage = portfolio.get('leverage', 1.0)
        checks['leverage']['value'] = current_leverage
        if current_leverage > self.risk_limits['max_leverage']:
            checks['leverage']['status'] = 'FAIL'
        elif current_leverage > self.risk_limits['max_leverage'] * 0.8:
            checks['leverage']['status'] = 'WARNING'
        
        return checks
    
    def _calculate_risk_metrics(
        self,
        strategy: Dict[str, Any],
        df,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate various risk metrics."""
        metrics = {
            'var_95': 0,
            'cvar_95': 0,
            'max_drawdown': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'beta': 1.0,
            'concentration_risk': 0,
            'liquidity_score': 100
        }
        
        if df is None or df.empty:
            return metrics
        
        try:
            close = df['close_price'].values
            returns = np.diff(close) / close[:-1]
            
            # Value at Risk (95%)
            var_95 = np.percentile(returns, 5)
            metrics['var_95'] = float(abs(var_95) * 100)
            
            # Conditional VaR (Expected Shortfall)
            cvar_95 = returns[returns <= var_95].mean()
            metrics['cvar_95'] = float(abs(cvar_95) * 100) if not np.isnan(cvar_95) else metrics['var_95']
            
            # Maximum Drawdown
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_dd = abs(drawdown.min())
            metrics['max_drawdown'] = float(max_dd * 100)
            
            # Volatility (annualized)
            volatility = np.std(returns) * np.sqrt(252)
            metrics['volatility'] = float(volatility * 100)
            
            # Sharpe Ratio (assuming 0 risk-free rate)
            avg_return = np.mean(returns)
            if volatility > 0:
                sharpe = (avg_return * 252) / volatility
                metrics['sharpe_ratio'] = float(sharpe)
            
            # Sortino Ratio (downside deviation)
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = np.std(downside_returns) * np.sqrt(252)
                if downside_std > 0:
                    sortino = (avg_return * 252) / downside_std
                    metrics['sortino_ratio'] = float(sortino)
            
            # Position concentration risk
            position_size = strategy.get('position_size', 0)
            if position_size > 0.25:
                metrics['concentration_risk'] = 100
            elif position_size > 0.15:
                metrics['concentration_risk'] = 60
            elif position_size > 0.10:
                metrics['concentration_risk'] = 30
            else:
                metrics['concentration_risk'] = 10
            
            # Liquidity score (based on volume stability)
            if 'volume' in df.columns:
                volume = df['volume'].values
                vol_std = np.std(volume) / np.mean(volume) if np.mean(volume) > 0 else 1
                metrics['liquidity_score'] = float(max(0, 100 - vol_std * 100))
        
        except Exception as e:
            print(f"⚠️  风险指标计算时出错: {e}")
        
        return metrics
    
    def _assess_overall_risk(
        self,
        strategy: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        compliance_check: Dict[str, Any]
    ) -> tuple:
        """Assess overall risk score and level."""
        risk_score = 0
        
        # VaR contribution (0-25 points)
        var_95 = risk_metrics.get('var_95', 0)
        if var_95 > self.risk_limits['var_95_limit'] * 100:
            risk_score += 25
        elif var_95 > self.risk_limits['var_95_limit'] * 80:
            risk_score += 15
        elif var_95 > self.risk_limits['var_95_limit'] * 50:
            risk_score += 8
        
        # Max drawdown contribution (0-20 points)
        max_dd = risk_metrics.get('max_drawdown', 0)
        if max_dd > self.risk_limits['max_drawdown'] * 100:
            risk_score += 20
        elif max_dd > self.risk_limits['max_drawdown'] * 80:
            risk_score += 12
        elif max_dd > self.risk_limits['max_drawdown'] * 50:
            risk_score += 6
        
        # Volatility contribution (0-15 points)
        volatility = risk_metrics.get('volatility', 0)
        if volatility > 40:
            risk_score += 15
        elif volatility > 30:
            risk_score += 10
        elif volatility > 20:
            risk_score += 5
        
        # Concentration risk contribution (0-15 points)
        concentration = risk_metrics.get('concentration_risk', 0)
        risk_score += concentration * 0.15
        
        # Compliance violations contribution (0-25 points)
        violations = sum(1 for check in compliance_check.values() 
                        if isinstance(check, dict) and check.get('status') == 'FAIL')
        warnings_count = sum(1 for check in compliance_check.values() 
                           if isinstance(check, dict) and check.get('status') == 'WARNING')
        risk_score += violations * 25
        risk_score += warnings_count * 10
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = 'CRITICAL'
        elif risk_score >= 50:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return float(min(100, risk_score)), risk_level
    
    def _identify_violations(
        self,
        compliance_check: Dict[str, Any],
        risk_metrics: Dict[str, Any]
    ) -> List[str]:
        """Identify compliance violations."""
        violations = []
        
        # Check compliance failures
        for name, check in compliance_check.items():
            if isinstance(check, dict) and check.get('status') == 'FAIL':
                if name == 'position_size':
                    violations.append(
                        f"仓位超限: {check['value']*100:.1f}% > {check['limit']*100:.1f}%"
                    )
                elif name == 'leverage':
                    violations.append(
                        f"杠杆超限: {check['value']:.1f}x > {check['limit']:.1f}x"
                    )
        
        # Check risk metric violations
        if risk_metrics.get('max_drawdown', 0) > self.risk_limits['max_drawdown'] * 100:
            violations.append(
                f"最大回撤超限: {risk_metrics['max_drawdown']:.1f}% > {self.risk_limits['max_drawdown']*100:.1f}%"
            )
        
        if risk_metrics.get('var_95', 0) > self.risk_limits['var_95_limit'] * 100:
            violations.append(
                f"VaR超限: {risk_metrics['var_95']:.1f}% > {self.risk_limits['var_95_limit']*100:.1f}%"
            )
        
        return violations
    
    def _generate_warnings(
        self,
        risk_metrics: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> List[str]:
        """Generate risk warnings."""
        warnings = []
        
        # High volatility warning
        volatility = risk_metrics.get('volatility', 0)
        if volatility > 35:
            warnings.append(f"⚠️  高波动率预警: {volatility:.1f}%, 市场不确定性大")
        
        # High concentration warning
        concentration = risk_metrics.get('concentration_risk', 0)
        if concentration > 60:
            warnings.append("⚠️  仓位集中度过高，缺乏分散化")
        
        # Low Sharpe ratio warning
        sharpe = risk_metrics.get('sharpe_ratio', 0)
        if sharpe < 0.5:
            warnings.append(f"⚠️  夏普比率偏低({sharpe:.2f}), 风险调整收益不佳")
        
        # Large position size warning
        position_size = strategy.get('position_size', 0)
        if position_size > 0.25:
            warnings.append(f"⚠️  单一仓位较大({position_size*100:.1f}%), 建议分批建仓")
        
        # No stop loss warning
        if not strategy.get('stop_loss'):
            warnings.append("⚠️  未设置止损，风险敞口不可控")
        
        # Low liquidity warning
        liquidity_score = risk_metrics.get('liquidity_score', 100)
        if liquidity_score < 50:
            warnings.append(f"⚠️  流动性不足({liquidity_score:.0f}/100), 可能难以平仓")
        
        if not warnings:
            warnings.append("✓ 当前无重大风险预警")
        
        return warnings
    
    def _determine_approval_status(
        self,
        violations: List[str],
        risk_score: float
    ) -> str:
        """Determine whether to approve the strategy."""
        if violations:
            return 'REJECTED'
        elif risk_score >= 60:
            return 'CONDITIONAL'
        else:
            return 'APPROVED'
    
    def _generate_recommendations(
        self,
        violations: List[str],
        warnings: List[str],
        risk_metrics: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if violations:
            recommendations.append("🔴 严重违规，必须整改后才能执行")
            
            # Specific fixes for violations
            for violation in violations:
                if "仓位超限" in violation:
                    recommendations.append(
                        f"→ 降低仓位至{self.risk_limits['max_position_size']*100:.0f}%以下"
                    )
                if "杠杆超限" in violation:
                    recommendations.append(
                        f"→ 降低杠杆至{self.risk_limits['max_leverage']:.1f}x以下"
                    )
                if "回撤超限" in violation:
                    recommendations.append(
                        f"→ 收紧止损线，控制最大回撤在{self.risk_limits['max_drawdown']*100:.0f}%以内"
                    )
        
        # Risk mitigation recommendations
        if risk_metrics.get('concentration_risk', 0) > 60:
            recommendations.append("→ 建议分散投资，降低仓位集中度")
        
        if risk_metrics.get('volatility', 0) > 35:
            recommendations.append("→ 建议降低仓位或使用期权对冲波动风险")
        
        if not strategy.get('stop_loss'):
            recommendations.append("→ 强制要求设置止损线，建议止损幅度5-10%")
        
        position_size = strategy.get('position_size', 0)
        if position_size > 0.20:
            recommendations.append("→ 建议分3-5次分批建仓，降低择时风险")
        
        if not recommendations:
            recommendations.append("✓ 风险可控，可以按计划执行")
            recommendations.append("→ 建议严格执行止损策略")
            recommendations.append("→ 定期监控风险指标变化")
        
        return recommendations
    
    def _build_analysis_prompt(
        self,
        strategy: Dict[str, Any],
        compliance_check: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        risk_score: float,
        risk_level: str,
        approval_status: str,
        violations: List[str],
        warnings: List[str],
        recommendations: List[str]
    ) -> str:
        """Build prompt for LLM analysis."""
        prompt = f"""# 风险控制审核报告

## 一、审核结论

- **审核状态**: **{approval_status}**
- **风险评分**: {risk_score:.1f}/100
- **风险等级**: **{risk_level}**

## 二、策略概览

- 策略类型: {strategy.get('strategy_type', 'N/A')}
- 操作建议: {strategy.get('action', 'N/A')}
- 建议仓位: {strategy.get('position_size', 0)*100:.1f}%
- 进场价格: {strategy.get('entry_price', 'N/A')}
- 止损价位: {strategy.get('stop_loss', 'N/A')}
- 止盈价位: {strategy.get('take_profit', 'N/A')}

## 三、合规检查

### 仓位检查
- 状态: {compliance_check['position_size']['status']}
- 当前: {compliance_check['position_size']['value']*100:.1f}%
- 限额: {compliance_check['position_size']['limit']*100:.1f}%

### 止损检查
- 状态: {compliance_check['stop_loss']['status']}
- 是否设置: {'是' if compliance_check['stop_loss']['exists'] else '否'}
"""
        if compliance_check['stop_loss'].get('value'):
            prompt += f"- 止损幅度: {compliance_check['stop_loss']['value']*100:.1f}%\n"
        
        prompt += f"""
### 杠杆检查
- 状态: {compliance_check['leverage']['status']}
- 当前: {compliance_check['leverage']['value']:.1f}x
- 限额: {compliance_check['leverage']['limit']:.1f}x

## 四、风险指标

### 市场风险
- VaR(95%): {risk_metrics['var_95']:.2f}%
- CVaR(95%): {risk_metrics['cvar_95']:.2f}%
- 最大回撤: {risk_metrics['max_drawdown']:.2f}%
- 波动率(年化): {risk_metrics['volatility']:.2f}%

### 风险调整收益
- 夏普比率: {risk_metrics['sharpe_ratio']:.3f}
- 索提诺比率: {risk_metrics['sortino_ratio']:.3f}

### 集中度与流动性
- 仓位集中度风险: {risk_metrics['concentration_risk']:.0f}/100
- 流动性评分: {risk_metrics['liquidity_score']:.0f}/100

## 五、违规事项
"""
        if violations:
            for violation in violations:
                prompt += f"🔴 {violation}\n"
        else:
            prompt += "✅ 无违规事项\n"
        
        prompt += "\n## 六、风险预警\n\n"
        for warning in warnings:
            prompt += f"{warning}\n"
        
        prompt += "\n## 七、整改建议\n\n"
        for rec in recommendations:
            prompt += f"{rec}\n"
        
        prompt += """
---

请基于以上风险和合规数据，从风险控制专员的角度进行严格审核：
1. 评估策略的整体风险水平和合规性
2. 分析各项风险指标是否在可接受范围内
3. 识别潜在的风险隐患和漏洞
4. 给出明确的审核意见（批准/有条件批准/拒绝）
5. 提出具体的风险控制和整改措施

要求：
- 报告必须简洁自然，控制在500字以内
- 严格执行风险限额
- 零容忍违规行为
- 保守评估风险
- 给出可执行的整改方案
- 保护资金安全是第一要务
"""
        return prompt
    
    def _extract_key_findings(
        self,
        approval_status: str,
        risk_level: str,
        violations: List[str],
        warnings: List[str]
    ) -> List[str]:
        """Extract key findings from risk control analysis."""
        findings = []
        
        findings.append(f"审核状态: {approval_status}")
        findings.append(f"风险等级: {risk_level}")
        
        if violations:
            findings.append(f"发现 {len(violations)} 项严重违规")
            findings.extend(violations[:2])
        else:
            findings.append("✓ 无合规违规")
        
        # Add top warnings
        warning_count = len([w for w in warnings if w.startswith("⚠️")])
        if warning_count > 0:
            findings.append(f"存在 {warning_count} 项风险预警")
        
        return findings
