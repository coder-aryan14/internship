"""
Sales Data Analysis and Business Insights Report
================================================
A comprehensive analysis tool for sales data that provides:
- Top products analysis (by revenue and quantity)
- Monthly trends and patterns
- Business insights and recommendations
- Professional visualizations and reports
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configure matplotlib for better quality outputs
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except OSError:
    try:
        plt.style.use('seaborn-darkgrid')
    except OSError:
        plt.style.use('default')
sns.set_palette("husl")

class SalesAnalyzer:
    """
    A comprehensive sales data analyzer class.
    """
    
    def __init__(self, data_path='sales_data.csv'):
        """
        Initialize the SalesAnalyzer with data path.
        
        Parameters:
        -----------
        data_path : str
            Path to the sales data CSV file
        """
        self.data_path = data_path
        self.df = None
        self.insights = []
        
    def load_data(self):
        """Load and preprocess sales data."""
        try:
            print("=" * 80)
            print("LOADING SALES DATA")
            print("=" * 80)
            
            self.df = pd.read_csv(self.data_path)
            
            # Convert Date to datetime
            self.df['Date'] = pd.to_datetime(self.df['Date'])
            
            # Extract additional date features
            self.df['Year'] = self.df['Date'].dt.year
            self.df['Month'] = self.df['Date'].dt.month
            self.df['Year_Month'] = self.df['Date'].dt.to_period('M')
            self.df['Month_Name'] = self.df['Date'].dt.strftime('%B')
            self.df['Quarter'] = self.df['Date'].dt.quarter
            self.df['Year_Quarter'] = self.df['Date'].dt.to_period('Q')
            self.df['Day_of_Week'] = self.df['Date'].dt.day_name()
            
            # Data validation
            self.df = self.df[self.df['Revenue'] > 0]  # Remove invalid records
            
            print(f"✓ Data loaded successfully")
            print(f"  - Total records: {len(self.df):,}")
            print(f"  - Date range: {self.df['Date'].min().strftime('%Y-%m-%d')} to {self.df['Date'].max().strftime('%Y-%m-%d')}")
            print(f"  - Unique products: {self.df['Product'].nunique()}")
            print(f"  - Unique customers: {self.df['Customer_ID'].nunique()}")
            print(f"  - Total revenue: ${self.df['Revenue'].sum():,.2f}\n")
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading data: {str(e)}")
            return False
    
    def analyze_top_products(self, top_n=10):
        """
        Analyze top products by revenue and quantity.
        
        Parameters:
        -----------
        top_n : int
            Number of top products to analyze
        """
        print("=" * 80)
        print("TOP PRODUCTS ANALYSIS")
        print("=" * 80)
        
        # Top products by revenue
        top_revenue = self.df.groupby('Product').agg({
            'Revenue': 'sum',
            'Quantity': 'sum',
            'Sale_ID': 'count'
        }).reset_index()
        top_revenue.columns = ['Product', 'Total_Revenue', 'Total_Quantity', 'Number_of_Sales']
        top_revenue = top_revenue.sort_values('Total_Revenue', ascending=False).head(top_n)
        
        # Top products by quantity
        top_quantity = self.df.groupby('Product').agg({
            'Quantity': 'sum',
            'Revenue': 'sum',
            'Sale_ID': 'count'
        }).reset_index()
        top_quantity.columns = ['Product', 'Total_Quantity', 'Total_Revenue', 'Number_of_Sales']
        top_quantity = top_quantity.sort_values('Total_Quantity', ascending=False).head(top_n)
        
        print("\n📊 TOP PRODUCTS BY REVENUE:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Product':<30} {'Revenue':<15} {'Quantity':<12} {'Sales':<10}")
        print("-" * 80)
        for idx, row in enumerate(top_revenue.itertuples(), 1):
            print(f"{idx:<6} {row.Product:<30} ${row.Total_Revenue:>12,.2f} {row.Total_Quantity:>10,} {row.Number_of_Sales:>8,}")
        
        print("\n📦 TOP PRODUCTS BY QUANTITY:")
        print("-" * 80)
        print(f"{'Rank':<6} {'Product':<30} {'Quantity':<12} {'Revenue':<15} {'Sales':<10}")
        print("-" * 80)
        for idx, row in enumerate(top_quantity.itertuples(), 1):
            print(f"{idx:<6} {row.Product:<30} {row.Total_Quantity:>10,} ${row.Total_Revenue:>12,.2f} {row.Number_of_Sales:>8,}")
        
        # Store insights
        top_product_revenue = top_revenue.iloc[0]['Product']
        top_product_qty = top_quantity.iloc[0]['Product']
        
        self.insights.append({
            'metric': 'Top Product by Revenue',
            'value': top_product_revenue,
            'details': f"Generated ${top_revenue.iloc[0]['Total_Revenue']:,.2f} in revenue"
        })
        
        # Calculate revenue concentration
        total_revenue = self.df['Revenue'].sum()
        top5_revenue_pct = (top_revenue.head(5)['Total_Revenue'].sum() / total_revenue) * 100
        self.insights.append({
            'metric': 'Revenue Concentration (Top 5)',
            'value': f"{top5_revenue_pct:.1f}%",
            'details': f"Top 5 products account for {top5_revenue_pct:.1f}% of total revenue"
        })
        
        return top_revenue, top_quantity
    
    def analyze_monthly_trends(self):
        """Analyze monthly sales trends."""
        print("\n" + "=" * 80)
        print("MONTHLY TRENDS ANALYSIS")
        print("=" * 80)
        
        # Monthly aggregation
        monthly_data = self.df.groupby('Year_Month').agg({
            'Revenue': ['sum', 'mean'],
            'Quantity': 'sum',
            'Sale_ID': 'count',
            'Unit_Price': 'mean'
        }).reset_index()
        
        monthly_data.columns = ['Year_Month', 'Total_Revenue', 'Avg_Transaction', 
                                'Total_Quantity', 'Number_of_Sales', 'Avg_Price']
        monthly_data = monthly_data.sort_values('Year_Month')
        
        print("\n📈 MONTHLY SALES SUMMARY:")
        print("-" * 80)
        print(f"{'Period':<15} {'Revenue':<15} {'Quantity':<12} {'Transactions':<12} {'Avg Order':<12}")
        print("-" * 80)
        for _, row in monthly_data.iterrows():
            print(f"{str(row['Year_Month']):<15} ${row['Total_Revenue']:>12,.2f} {row['Total_Quantity']:>10,} "
                  f"{row['Number_of_Sales']:>10,} ${row['Avg_Transaction']:>10,.2f}")
        
        # Calculate growth rates
        monthly_data['Revenue_Growth'] = monthly_data['Total_Revenue'].pct_change() * 100
        monthly_data['Sales_Growth'] = monthly_data['Number_of_Sales'].pct_change() * 100
        
        # Best and worst months
        best_month = monthly_data.loc[monthly_data['Total_Revenue'].idxmax()]
        worst_month = monthly_data.loc[monthly_data['Total_Revenue'].idxmin()]
        
        print(f"\n🏆 BEST PERFORMING MONTH: {best_month['Year_Month']}")
        print(f"   Revenue: ${best_month['Total_Revenue']:,.2f}")
        print(f"   Transactions: {best_month['Number_of_Sales']:,}")
        
        print(f"\n📉 LOWEST PERFORMING MONTH: {worst_month['Year_Month']}")
        print(f"   Revenue: ${worst_month['Total_Revenue']:,.2f}")
        print(f"   Transactions: {worst_month['Number_of_Sales']:,}")
        
        # Year-over-year comparison
        yearly_data = self.df.groupby('Year').agg({
            'Revenue': 'sum',
            'Quantity': 'sum',
            'Sale_ID': 'count'
        }).reset_index()
        
        if len(yearly_data) > 1:
            yoy_growth = ((yearly_data.iloc[-1]['Revenue'] - yearly_data.iloc[-2]['Revenue']) / 
                         yearly_data.iloc[-2]['Revenue']) * 100
            print(f"\n📊 YEAR-OVER-YEAR GROWTH: {yoy_growth:.1f}%")
            
            self.insights.append({
                'metric': 'Year-over-Year Growth',
                'value': f"{yoy_growth:.1f}%",
                'details': f"Revenue growth from {yearly_data.iloc[-2]['Year']} to {yearly_data.iloc[-1]['Year']}"
            })
        
        # Store insights
        avg_monthly_revenue = monthly_data['Total_Revenue'].mean()
        self.insights.append({
            'metric': 'Average Monthly Revenue',
            'value': f"${avg_monthly_revenue:,.2f}",
            'details': f"Average revenue per month across all periods"
        })
        
        return monthly_data, yearly_data
    
    def analyze_category_performance(self):
        """Analyze performance by product category."""
        print("\n" + "=" * 80)
        print("CATEGORY PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        category_data = self.df.groupby('Category').agg({
            'Revenue': 'sum',
            'Quantity': 'sum',
            'Sale_ID': 'count',
            'Unit_Price': 'mean'
        }).reset_index()
        category_data.columns = ['Category', 'Total_Revenue', 'Total_Quantity', 
                                 'Number_of_Sales', 'Avg_Price']
        category_data = category_data.sort_values('Total_Revenue', ascending=False)
        
        print(f"\n{'Category':<20} {'Revenue':<15} {'Quantity':<12} {'Sales':<10} {'Avg Price':<12}")
        print("-" * 80)
        for _, row in category_data.iterrows():
            print(f"{row['Category']:<20} ${row['Total_Revenue']:>12,.2f} {row['Total_Quantity']:>10,} "
                  f"{row['Number_of_Sales']:>10,} ${row['Avg_Price']:>10,.2f}")
        
        top_category = category_data.iloc[0]
        self.insights.append({
            'metric': 'Top Category by Revenue',
            'value': top_category['Category'],
            'details': f"Generated ${top_category['Total_Revenue']:,.2f} in revenue"
        })
        
        return category_data
    
    def create_visualizations(self):
        """Create professional visualizations."""
        print("\n" + "=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)
        
        # Create figure with subplots
        fig = plt.figure(figsize=(20, 12))
        
        # 1. Top Products by Revenue
        ax1 = plt.subplot(3, 3, 1)
        top_revenue = self.df.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(10)
        colors = plt.cm.viridis(np.linspace(0, 1, len(top_revenue)))
        bars1 = ax1.barh(range(len(top_revenue)), top_revenue.values, color=colors)
        ax1.set_yticks(range(len(top_revenue)))
        ax1.set_yticklabels(top_revenue.index, fontsize=8)
        ax1.set_xlabel('Revenue ($)', fontweight='bold')
        ax1.set_title('Top 10 Products by Revenue', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        # Add value labels
        for i, (idx, val) in enumerate(top_revenue.items()):
            ax1.text(val, i, f'${val:,.0f}', va='center', fontsize=7)
        
        # 2. Monthly Revenue Trend
        ax2 = plt.subplot(3, 3, 2)
        monthly_revenue = self.df.groupby('Year_Month')['Revenue'].sum()
        ax2.plot(range(len(monthly_revenue)), monthly_revenue.values, 
                marker='o', linewidth=2, markersize=6, color='#2E86AB')
        ax2.set_xticks(range(0, len(monthly_revenue), max(1, len(monthly_revenue)//10)))
        ax2.set_xticklabels([str(x) for x in monthly_revenue.index[::max(1, len(monthly_revenue)//10)]], 
                           rotation=45, ha='right', fontsize=7)
        ax2.set_ylabel('Revenue ($)', fontweight='bold')
        ax2.set_title('Monthly Revenue Trend', fontsize=12, fontweight='bold')
        ax2.grid(alpha=0.3)
        
        # 3. Monthly Transaction Count
        ax3 = plt.subplot(3, 3, 3)
        monthly_sales = self.df.groupby('Year_Month')['Sale_ID'].count()
        ax3.bar(range(len(monthly_sales)), monthly_sales.values, color='#A23B72', alpha=0.7)
        ax3.set_xticks(range(0, len(monthly_sales), max(1, len(monthly_sales)//10)))
        ax3.set_xticklabels([str(x) for x in monthly_sales.index[::max(1, len(monthly_sales)//10)]], 
                           rotation=45, ha='right', fontsize=7)
        ax3.set_ylabel('Number of Sales', fontweight='bold')
        ax3.set_title('Monthly Transaction Volume', fontsize=12, fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        
        # 4. Category Revenue Distribution
        ax4 = plt.subplot(3, 3, 4)
        category_revenue = self.df.groupby('Category')['Revenue'].sum().sort_values(ascending=False)
        colors_cat = plt.cm.Set3(np.linspace(0, 1, len(category_revenue)))
        wedges, texts, autotexts = ax4.pie(category_revenue.values, labels=category_revenue.index, 
                                          autopct='%1.1f%%', colors=colors_cat, startangle=90)
        ax4.set_title('Revenue by Category', fontsize=12, fontweight='bold')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        # 5. Top Products by Quantity
        ax5 = plt.subplot(3, 3, 5)
        top_quantity = self.df.groupby('Product')['Quantity'].sum().sort_values(ascending=False).head(10)
        bars5 = ax5.bar(range(len(top_quantity)), top_quantity.values, color='#F18F01')
        ax5.set_xticks(range(len(top_quantity)))
        ax5.set_xticklabels(top_quantity.index, rotation=45, ha='right', fontsize=7)
        ax5.set_ylabel('Quantity Sold', fontweight='bold')
        ax5.set_title('Top 10 Products by Quantity', fontsize=12, fontweight='bold')
        ax5.grid(axis='y', alpha=0.3)
        # Add value labels
        for i, (idx, val) in enumerate(top_quantity.items()):
            ax5.text(i, val, f'{int(val)}', ha='center', va='bottom', fontsize=7)
        
        # 6. Revenue by Region
        ax6 = plt.subplot(3, 3, 6)
        region_revenue = self.df.groupby('Region')['Revenue'].sum().sort_values(ascending=False)
        bars6 = ax6.bar(region_revenue.index, region_revenue.values, color='#C73E1D', alpha=0.8)
        ax6.set_ylabel('Revenue ($)', fontweight='bold')
        ax6.set_title('Revenue by Region', fontsize=12, fontweight='bold')
        ax6.grid(axis='y', alpha=0.3)
        # Add value labels
        for i, (region, val) in enumerate(region_revenue.items()):
            ax6.text(i, val, f'${val:,.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        # 7. Average Transaction Value Over Time
        ax7 = plt.subplot(3, 3, 7)
        monthly_avg = self.df.groupby('Year_Month')['Revenue'].mean()
        ax7.plot(range(len(monthly_avg)), monthly_avg.values, 
                marker='s', linewidth=2, markersize=5, color='#6A994E')
        ax7.set_xticks(range(0, len(monthly_avg), max(1, len(monthly_avg)//10)))
        ax7.set_xticklabels([str(x) for x in monthly_avg.index[::max(1, len(monthly_avg)//10)]], 
                           rotation=45, ha='right', fontsize=7)
        ax7.set_ylabel('Average Transaction ($)', fontweight='bold')
        ax7.set_title('Average Transaction Value Trend', fontsize=12, fontweight='bold')
        ax7.grid(alpha=0.3)
        
        # 8. Sales by Day of Week
        ax8 = plt.subplot(3, 3, 8)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_revenue = self.df.groupby('Day_of_Week')['Revenue'].sum()
        day_revenue = day_revenue.reindex([d for d in day_order if d in day_revenue.index])
        bars8 = ax8.bar(day_revenue.index, day_revenue.values, color='#BC4749', alpha=0.7)
        ax8.set_xticklabels(day_revenue.index, rotation=45, ha='right', fontsize=8)
        ax8.set_ylabel('Revenue ($)', fontweight='bold')
        ax8.set_title('Revenue by Day of Week', fontsize=12, fontweight='bold')
        ax8.grid(axis='y', alpha=0.3)
        
        # 9. Quarterly Comparison
        ax9 = plt.subplot(3, 3, 9)
        quarterly_revenue = self.df.groupby('Year_Quarter')['Revenue'].sum()
        bars9 = ax9.bar(range(len(quarterly_revenue)), quarterly_revenue.values, 
                       color='#4A90E2', alpha=0.8)
        ax9.set_xticks(range(len(quarterly_revenue)))
        ax9.set_xticklabels([str(x) for x in quarterly_revenue.index], 
                           rotation=45, ha='right', fontsize=7)
        ax9.set_ylabel('Revenue ($)', fontweight='bold')
        ax9.set_title('Quarterly Revenue Comparison', fontsize=12, fontweight='bold')
        ax9.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('sales_analysis_report.png', dpi=300, bbox_inches='tight')
        print("✓ Visualizations saved as 'sales_analysis_report.png'")
        
        plt.close()
    
    def generate_business_insights(self):
        """Generate comprehensive business insights and recommendations."""
        print("\n" + "=" * 80)
        print("BUSINESS INSIGHTS & RECOMMENDATIONS")
        print("=" * 80)
        
        total_revenue = self.df['Revenue'].sum()
        total_transactions = len(self.df)
        avg_transaction = total_revenue / total_transactions
        unique_customers = self.df['Customer_ID'].nunique()
        unique_products = self.df['Product'].nunique()
        
        # Calculate additional metrics
        top_product_rev = self.df.groupby('Product')['Revenue'].sum().max()
        top_product_rev_pct = (top_product_rev / total_revenue) * 100
        
        # Monthly trend analysis
        monthly_revenue = self.df.groupby('Year_Month')['Revenue'].sum()
        recent_months = monthly_revenue.tail(3)
        older_months = monthly_revenue.iloc[-6:-3] if len(monthly_revenue) >= 6 else monthly_revenue.iloc[:3]
        
        if len(recent_months) > 0 and len(older_months) > 0:
            recent_avg = recent_months.mean()
            older_avg = older_months.mean()
            trend_direction = "increasing" if recent_avg > older_avg else "decreasing"
            trend_pct = abs((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        else:
            trend_direction = "stable"
            trend_pct = 0
        
        # Region analysis
        region_revenue = self.df.groupby('Region')['Revenue'].sum()
        top_region = region_revenue.idxmax()
        top_region_pct = (region_revenue.max() / total_revenue) * 100
        
        # Category analysis
        category_revenue = self.df.groupby('Category')['Revenue'].sum()
        top_category = category_revenue.idxmax()
        
        print(f"""
═══════════════════════════════════════════════════════════════════════════════
                              EXECUTIVE SUMMARY
═══════════════════════════════════════════════════════════════════════════════

📊 KEY PERFORMANCE INDICATORS:
   • Total Revenue:              ${total_revenue:,.2f}
   • Total Transactions:         {total_transactions:,}
   • Average Transaction Value:  ${avg_transaction:.2f}
   • Unique Customers:           {unique_customers:,}
   • Product Portfolio Size:     {unique_products} products

📈 PERFORMANCE TRENDS:
   • Revenue Trend:              {trend_direction.capitalize()} ({trend_pct:.1f}% change)
   • Top Product Contribution:   {top_product_rev_pct:.1f}% of total revenue
   • Best Performing Region:     {top_region} ({top_region_pct:.1f}% of revenue)
   • Leading Category:           {top_category}

💡 STRATEGIC INSIGHTS:

1. PRODUCT PERFORMANCE:
   • Focus marketing efforts on top-performing products to maximize revenue
   • Consider bundling strategies for complementary products
   • Review low-performing products for potential discontinuation or promotion

2. TREND ANALYSIS:
   • Monitor monthly trends closely to identify seasonal patterns
   • Implement strategies to boost performance in slower months
   • Capitalize on high-performing periods with increased inventory and marketing

3. MARKET SEGMENTATION:
   • Regional performance varies significantly - develop region-specific strategies
   • Category analysis reveals customer preferences - adjust inventory accordingly
   • Customer base analysis can identify opportunities for upselling and retention

4. RECOMMENDATIONS:
   ✓ Increase inventory of top-selling products
   ✓ Develop targeted marketing campaigns for underperforming regions
   ✓ Create product bundles to increase average transaction value
   ✓ Implement loyalty programs to improve customer retention
   ✓ Analyze customer purchase patterns for cross-selling opportunities
   ✓ Optimize pricing strategy based on product performance
   ✓ Plan promotional campaigns around slow periods

═══════════════════════════════════════════════════════════════════════════════
""")
        
        return {
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'avg_transaction': avg_transaction,
            'unique_customers': unique_customers,
            'unique_products': unique_products
        }
    
    def export_summary_report(self, filename='business_insights_report.txt'):
        """Export a detailed text report."""
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("SALES DATA ANALYSIS - BUSINESS INSIGHTS REPORT\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary statistics
            total_revenue = self.df['Revenue'].sum()
            total_transactions = len(self.df)
            avg_transaction = total_revenue / total_transactions
            
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Revenue: ${total_revenue:,.2f}\n")
            f.write(f"Total Transactions: {total_transactions:,}\n")
            f.write(f"Average Transaction Value: ${avg_transaction:.2f}\n")
            f.write(f"Date Range: {self.df['Date'].min().strftime('%Y-%m-%d')} to {self.df['Date'].max().strftime('%Y-%m-%d')}\n\n")
            
            # Top products
            f.write("TOP PRODUCTS BY REVENUE\n")
            f.write("-" * 80 + "\n")
            top_revenue = self.df.groupby('Product')['Revenue'].sum().sort_values(ascending=False).head(10)
            for idx, (product, revenue) in enumerate(top_revenue.items(), 1):
                f.write(f"{idx}. {product}: ${revenue:,.2f}\n")
            
            f.write("\n")
            
            # Monthly trends
            f.write("MONTHLY REVENUE SUMMARY\n")
            f.write("-" * 80 + "\n")
            monthly_revenue = self.df.groupby('Year_Month')['Revenue'].sum().sort_index()
            for period, revenue in monthly_revenue.items():
                f.write(f"{period}: ${revenue:,.2f}\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        print(f"✓ Detailed report exported to '{filename}'")
    
    def run_full_analysis(self):
        """Execute complete analysis pipeline."""
        if not self.load_data():
            return False
        
        print("\n" + "🔍 " * 40)
        print("STARTING COMPREHENSIVE ANALYSIS...")
        print("🔍 " * 40 + "\n")
        
        # Run all analyses
        top_revenue, top_quantity = self.analyze_top_products()
        monthly_data, yearly_data = self.analyze_monthly_trends()
        category_data = self.analyze_category_performance()
        self.create_visualizations()
        summary = self.generate_business_insights()
        self.export_summary_report()
        
        print("\n" + "=" * 80)
        print("✓ ANALYSIS COMPLETE - All reports and visualizations generated!")
        print("=" * 80)
        
        return True


def main():
    """Main execution function."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "SALES DATA ANALYSIS SYSTEM" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    analyzer = SalesAnalyzer('sales_data.csv')
    analyzer.run_full_analysis()
    
    print("\n📁 Generated Files:")
    print("   • sales_analysis_report.png - Comprehensive visualizations")
    print("   • business_insights_report.txt - Detailed text report\n")


if __name__ == "__main__":
    main()

