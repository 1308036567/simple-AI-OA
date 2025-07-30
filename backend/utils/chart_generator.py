from pyecharts import options as opts
from pyecharts.charts import Bar, Line, Pie, Scatter, Funnel, Gauge, Radar
from pyecharts.globals import ThemeType
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from models import SalaryRecord, ExpenseRecord, Employee, AccountTable

logger = logging.getLogger(__name__)

class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        self.theme = ThemeType.MACARONS
        self.default_width = "100%"
        self.default_height = "400px"
    
    def generate_salary_chart(self, salary_data: List[Dict[str, Any]], chart_type: str = 'bar') -> str:
        """
        生成工资图表
        
        Args:
            salary_data: 工资数据列表
            chart_type: 图表类型 ('bar', 'line', 'pie')
            
        Returns:
            图表HTML字符串
        """
        try:
            if not salary_data:
                return self._generate_empty_chart("暂无工资数据")
            
            if chart_type == 'bar':
                return self._generate_salary_bar_chart(salary_data)
            elif chart_type == 'line':
                return self._generate_salary_line_chart(salary_data)
            elif chart_type == 'pie':
                return self._generate_salary_pie_chart(salary_data)
            else:
                return self._generate_salary_bar_chart(salary_data)
                
        except Exception as e:
            logger.error(f"生成工资图表失败: {e}")
            return self._generate_error_chart("图表生成失败")
    
    def _generate_salary_bar_chart(self, salary_data: List[Dict[str, Any]]) -> str:
        """生成工资柱状图"""
        try:
            # 准备数据
            names = [item.get('employee_name', '未知') for item in salary_data]
            amounts = [float(item.get('salary_amount', 0)) for item in salary_data]
            bonuses = [float(item.get('bonus', 0)) for item in salary_data]
            deductions = [float(item.get('deduction', 0)) for item in salary_data]
            
            # 计算实发工资
            actual_salaries = [amounts[i] + bonuses[i] - deductions[i] for i in range(len(amounts))]
            
            # 创建柱状图
            bar = (
                Bar(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add_xaxis(names)
                .add_yaxis("基本工资", amounts, stack="stack1")
                .add_yaxis("奖金", bonuses, stack="stack1")
                .add_yaxis("扣款", [-d for d in deductions], stack="stack1")
                .add_yaxis("实发工资", actual_salaries, stack="stack2")
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="员工工资统计", subtitle="基本工资、奖金、扣款及实发工资对比"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
                    yaxis_opts=opts.AxisOpts(name="金额(元)"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross"),
                    legend_opts=opts.LegendOpts(pos_top="5%"),
                    datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)]
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(is_show=False),
                    markpoint_opts=opts.MarkPointOpts(
                        data=[
                            opts.MarkPointItem(type_="max", name="最大值"),
                            opts.MarkPointItem(type_="min", name="最小值")
                        ]
                    )
                )
            )
            
            return bar.render_embed()
            
        except Exception as e:
            logger.error(f"生成工资柱状图失败: {e}")
            return self._generate_error_chart("柱状图生成失败")
    
    def _generate_salary_line_chart(self, salary_data: List[Dict[str, Any]]) -> str:
        """生成工资折线图"""
        try:
            # 按日期排序数据
            sorted_data = sorted(salary_data, key=lambda x: x.get('pay_date', '2024-01-01'))
            
            dates = [item.get('pay_date', '未知日期') for item in sorted_data]
            amounts = [float(item.get('salary_amount', 0)) for item in sorted_data]
            
            # 创建折线图
            line = (
                Line(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add_xaxis(dates)
                .add_yaxis(
                    "工资趋势",
                    amounts,
                    is_smooth=True,
                    markpoint_opts=opts.MarkPointOpts(
                        data=[
                            opts.MarkPointItem(type_="max", name="最高工资"),
                            opts.MarkPointItem(type_="min", name="最低工资")
                        ]
                    ),
                    markline_opts=opts.MarkLineOpts(
                        data=[opts.MarkLineItem(type_="average", name="平均值")]
                    )
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="工资发放趋势", subtitle="按时间显示工资变化趋势"),
                    xaxis_opts=opts.AxisOpts(name="发放日期", axislabel_opts=opts.LabelOpts(rotate=-15)),
                    yaxis_opts=opts.AxisOpts(name="工资金额(元)"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)]
                )
            )
            
            return line.render_embed()
            
        except Exception as e:
            logger.error(f"生成工资折线图失败: {e}")
            return self._generate_error_chart("折线图生成失败")
    
    def _generate_salary_pie_chart(self, salary_data: List[Dict[str, Any]]) -> str:
        """生成工资饼图"""
        try:
            # 准备数据
            pie_data = [
                [item.get('employee_name', '未知'), float(item.get('salary_amount', 0))]
                for item in salary_data
            ]
            
            # 创建饼图
            pie = (
                Pie(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add(
                    "工资分布",
                    pie_data,
                    radius=["40%", "75%"],
                    center=["50%", "50%"],
                    rosetype="radius"
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="员工工资分布", subtitle="各员工工资占比"),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
                    tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(formatter="{b}: {d}%")
                )
            )
            
            return pie.render_embed()
            
        except Exception as e:
            logger.error(f"生成工资饼图失败: {e}")
            return self._generate_error_chart("饼图生成失败")
    
    def generate_expense_chart(self, expense_data: List[Dict[str, Any]], chart_type: str = 'bar') -> str:
        """
        生成支出图表
        
        Args:
            expense_data: 支出数据列表
            chart_type: 图表类型 ('bar', 'line', 'pie')
            
        Returns:
            图表HTML字符串
        """
        try:
            if not expense_data:
                return self._generate_empty_chart("暂无支出数据")
            
            if chart_type == 'bar':
                return self._generate_expense_bar_chart(expense_data)
            elif chart_type == 'line':
                return self._generate_expense_line_chart(expense_data)
            elif chart_type == 'pie':
                return self._generate_expense_pie_chart(expense_data)
            else:
                return self._generate_expense_bar_chart(expense_data)
                
        except Exception as e:
            logger.error(f"生成支出图表失败: {e}")
            return self._generate_error_chart("图表生成失败")
    
    def _generate_expense_bar_chart(self, expense_data: List[Dict[str, Any]]) -> str:
        """生成支出柱状图"""
        try:
            # 按支出类型分组
            expense_by_type = {}
            for item in expense_data:
                expense_type = item.get('expense_type', '其他')
                amount = float(item.get('amount', 0))
                if expense_type in expense_by_type:
                    expense_by_type[expense_type] += amount
                else:
                    expense_by_type[expense_type] = amount
            
            types = list(expense_by_type.keys())
            amounts = list(expense_by_type.values())
            
            # 创建柱状图
            bar = (
                Bar(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add_xaxis(types)
                .add_yaxis("支出金额", amounts)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="支出类型统计", subtitle="按支出类型分组的金额统计"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
                    yaxis_opts=opts.AxisOpts(name="金额(元)"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)]
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(is_show=True, position="top"),
                    markpoint_opts=opts.MarkPointOpts(
                        data=[
                            opts.MarkPointItem(type_="max", name="最大值"),
                            opts.MarkPointItem(type_="min", name="最小值")
                        ]
                    )
                )
            )
            
            return bar.render_embed()
            
        except Exception as e:
            logger.error(f"生成支出柱状图失败: {e}")
            return self._generate_error_chart("柱状图生成失败")
    
    def _generate_expense_line_chart(self, expense_data: List[Dict[str, Any]]) -> str:
        """生成支出折线图"""
        try:
            # 按日期排序并分组
            sorted_data = sorted(expense_data, key=lambda x: x.get('expense_date', '2024-01-01'))
            
            # 按日期汇总支出
            daily_expenses = {}
            for item in sorted_data:
                date = item.get('expense_date', '未知日期')
                amount = float(item.get('amount', 0))
                if date in daily_expenses:
                    daily_expenses[date] += amount
                else:
                    daily_expenses[date] = amount
            
            dates = list(daily_expenses.keys())
            amounts = list(daily_expenses.values())
            
            # 创建折线图
            line = (
                Line(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add_xaxis(dates)
                .add_yaxis(
                    "日支出",
                    amounts,
                    is_smooth=True,
                    markpoint_opts=opts.MarkPointOpts(
                        data=[
                            opts.MarkPointItem(type_="max", name="最高支出"),
                            opts.MarkPointItem(type_="min", name="最低支出")
                        ]
                    ),
                    markline_opts=opts.MarkLineOpts(
                        data=[opts.MarkLineItem(type_="average", name="平均值")]
                    )
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="支出趋势分析", subtitle="按日期显示支出变化趋势"),
                    xaxis_opts=opts.AxisOpts(name="支出日期", axislabel_opts=opts.LabelOpts(rotate=-15)),
                    yaxis_opts=opts.AxisOpts(name="支出金额(元)"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    datazoom_opts=[opts.DataZoomOpts(range_start=0, range_end=100)]
                )
            )
            
            return line.render_embed()
            
        except Exception as e:
            logger.error(f"生成支出折线图失败: {e}")
            return self._generate_error_chart("折线图生成失败")
    
    def _generate_expense_pie_chart(self, expense_data: List[Dict[str, Any]]) -> str:
        """生成支出饼图"""
        try:
            # 按支出类型分组
            expense_by_type = {}
            for item in expense_data:
                expense_type = item.get('expense_type', '其他')
                amount = float(item.get('amount', 0))
                if expense_type in expense_by_type:
                    expense_by_type[expense_type] += amount
                else:
                    expense_by_type[expense_type] = amount
            
            pie_data = [[k, v] for k, v in expense_by_type.items()]
            
            # 创建饼图
            pie = (
                Pie(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add(
                    "支出分布",
                    pie_data,
                    radius=["40%", "75%"],
                    center=["50%", "50%"]
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="支出类型分布", subtitle="各类型支出占比"),
                    legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
                    tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)")
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(formatter="{b}: {d}%")
                )
            )
            
            return pie.render_embed()
            
        except Exception as e:
            logger.error(f"生成支出饼图失败: {e}")
            return self._generate_error_chart("饼图生成失败")
    
    def generate_dashboard_chart(self, db: Session) -> str:
        """
        生成仪表盘图表
        
        Args:
            db: 数据库会话
            
        Returns:
            仪表盘HTML字符串
        """
        try:
            # 获取统计数据
            stats = self._get_dashboard_stats(db)
            
            # 创建仪表盘
            dashboard_html = self._create_dashboard_layout(stats)
            
            return dashboard_html
            
        except Exception as e:
            logger.error(f"生成仪表盘失败: {e}")
            return self._generate_error_chart("仪表盘生成失败")
    
    def _get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        try:
            # 员工统计
            total_employees = db.query(Employee).count()
            active_employees = db.query(Employee).filter(Employee.is_archived == False).count()
            
            # 本月工资统计
            current_month = datetime.now().strftime('%Y-%m')
            monthly_salary = db.query(SalaryRecord).filter(
                SalaryRecord.pay_date.like(f'{current_month}%')
            ).all()
            
            total_salary = sum(record.salary_amount + (record.bonus or 0) - (record.deduction or 0) 
                             for record in monthly_salary)
            
            # 本月支出统计
            monthly_expenses = db.query(ExpenseRecord).filter(
                ExpenseRecord.expense_date.like(f'{current_month}%')
            ).all()
            
            total_expense = sum(record.amount for record in monthly_expenses)
            
            # 账表统计
            total_accounts = db.query(AccountTable).count()
            
            return {
                'total_employees': total_employees,
                'active_employees': active_employees,
                'total_salary': total_salary,
                'total_expense': total_expense,
                'total_accounts': total_accounts,
                'current_month': current_month
            }
            
        except Exception as e:
            logger.error(f"获取仪表盘统计数据失败: {e}")
            return {}
    
    def _create_dashboard_layout(self, stats: Dict[str, Any]) -> str:
        """创建仪表盘布局"""
        try:
            # 创建仪表图
            gauge = (
                Gauge(init_opts=opts.InitOpts(theme=self.theme, width="300px", height="300px"))
                .add(
                    "员工活跃度",
                    [("活跃员工比例", stats.get('active_employees', 0) / max(stats.get('total_employees', 1), 1) * 100)],
                    radius="75%"
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="员工活跃度")
                )
            )
            
            # 创建资金流水图
            bar = (
                Bar(init_opts=opts.InitOpts(theme=self.theme, width="400px", height="300px"))
                .add_xaxis(["工资支出", "其他支出"])
                .add_yaxis("金额", [stats.get('total_salary', 0), stats.get('total_expense', 0)])
                .set_global_opts(
                    title_opts=opts.TitleOpts(title=f"{stats.get('current_month', '')}月资金流水"),
                    yaxis_opts=opts.AxisOpts(name="金额(元)")
                )
            )
            
            # 组合HTML
            dashboard_html = f"""
            <div style="display: flex; flex-wrap: wrap; gap: 20px; padding: 20px;">
                <div style="flex: 1; min-width: 300px;">
                    <h3>统计概览</h3>
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                        <p><strong>总员工数:</strong> {stats.get('total_employees', 0)}</p>
                        <p><strong>在职员工:</strong> {stats.get('active_employees', 0)}</p>
                        <p><strong>本月工资:</strong> ¥{stats.get('total_salary', 0):,.2f}</p>
                        <p><strong>本月支出:</strong> ¥{stats.get('total_expense', 0):,.2f}</p>
                        <p><strong>账表数量:</strong> {stats.get('total_accounts', 0)}</p>
                    </div>
                </div>
                <div style="flex: 1; min-width: 300px;">
                    {gauge.render_embed()}
                </div>
                <div style="flex: 1; min-width: 400px;">
                    {bar.render_embed()}
                </div>
            </div>
            """
            
            return dashboard_html
            
        except Exception as e:
            logger.error(f"创建仪表盘布局失败: {e}")
            return self._generate_error_chart("仪表盘布局创建失败")
    
    def generate_comparison_chart(self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]], 
                                title1: str = "数据1", title2: str = "数据2") -> str:
        """
        生成对比图表
        
        Args:
            data1: 第一组数据
            data2: 第二组数据
            title1: 第一组数据标题
            title2: 第二组数据标题
            
        Returns:
            对比图表HTML字符串
        """
        try:
            # 准备数据
            categories = list(set([item.get('category', '未知') for item in data1 + data2]))
            
            values1 = []
            values2 = []
            
            for category in categories:
                val1 = sum(item.get('value', 0) for item in data1 if item.get('category') == category)
                val2 = sum(item.get('value', 0) for item in data2 if item.get('category') == category)
                values1.append(val1)
                values2.append(val2)
            
            # 创建对比柱状图
            bar = (
                Bar(init_opts=opts.InitOpts(theme=self.theme, width=self.default_width, height=self.default_height))
                .add_xaxis(categories)
                .add_yaxis(title1, values1)
                .add_yaxis(title2, values2)
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="数据对比分析", subtitle=f"{title1} vs {title2}"),
                    xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15)),
                    yaxis_opts=opts.AxisOpts(name="数值"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                    legend_opts=opts.LegendOpts(pos_top="5%")
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(is_show=False)
                )
            )
            
            return bar.render_embed()
            
        except Exception as e:
            logger.error(f"生成对比图表失败: {e}")
            return self._generate_error_chart("对比图表生成失败")
    
    def _generate_empty_chart(self, message: str) -> str:
        """生成空数据图表"""
        return f"""
        <div style="display: flex; align-items: center; justify-content: center; 
                    height: 400px; background: #f5f5f5; border-radius: 8px;">
            <div style="text-align: center; color: #999;">
                <h3>{message}</h3>
                <p>暂时没有可显示的数据</p>
            </div>
        </div>
        """
    
    def _generate_error_chart(self, error_message: str) -> str:
        """生成错误图表"""
        return f"""
        <div style="display: flex; align-items: center; justify-content: center; 
                    height: 400px; background: #ffe6e6; border-radius: 8px; border: 1px solid #ffcccc;">
            <div style="text-align: center; color: #cc0000;">
                <h3>图表生成失败</h3>
                <p>{error_message}</p>
            </div>
        </div>
        """
    
    def export_chart_config(self, chart_type: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        导出图表配置
        
        Args:
            chart_type: 图表类型
            data: 图表数据
            
        Returns:
            图表配置字典
        """
        try:
            config = {
                'chart_type': chart_type,
                'data': data,
                'theme': self.theme,
                'width': self.default_width,
                'height': self.default_height,
                'created_at': datetime.now().isoformat()
            }
            
            return config
            
        except Exception as e:
            logger.error(f"导出图表配置失败: {e}")
            return {}
    
    def import_chart_config(self, config: Dict[str, Any]) -> str:
        """
        从配置导入图表
        
        Args:
            config: 图表配置
            
        Returns:
            图表HTML字符串
        """
        try:
            chart_type = config.get('chart_type', 'bar')
            data = config.get('data', [])
            
            if 'salary' in chart_type:
                return self.generate_salary_chart(data, chart_type.replace('salary_', ''))
            elif 'expense' in chart_type:
                return self.generate_expense_chart(data, chart_type.replace('expense_', ''))
            else:
                return self._generate_error_chart("不支持的图表类型")
                
        except Exception as e:
            logger.error(f"从配置导入图表失败: {e}")
            return self._generate_error_chart("图表导入失败")

def create_chart_generator() -> ChartGenerator:
    """创建图表生成器实例"""
    return ChartGenerator()

# 全局图表生成器实例
chart_generator = None

def get_chart_generator() -> ChartGenerator:
    """获取图表生成器实例"""
    global chart_generator
    if chart_generator is None:
        chart_generator = create_chart_generator()
    return chart_generator