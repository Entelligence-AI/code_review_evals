import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from typing import Dict, List

class ResultsVisualizer:
    @staticmethod
    def create_impact_distribution_chart(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Create a stacked bar chart showing comment category distribution by bot"""
        data = []
        for bot, scores in metrics.items():
            data.append({
                'Bot': bot,
                'Critical Bugs': scores['critical_bug_ratio'],
                'Nitpicks': scores['nitpick_ratio'],
                'Other': scores['other_ratio']
            })

        df = pd.DataFrame(data)

        # Set style
        plt.style.use('seaborn')
        plt.figure(figsize=(12, 6))

        # Create stacked bar chart
        ax = df.plot(
            x='Bot',
            y=['Critical Bugs', 'Nitpicks', 'Other'],
            kind='bar',
            stacked=True,
            color=['#ff6b6b', '#4ecdc4', '#45b7d1']
        )

        # Customize chart
        plt.title('Comment Category Distribution by Code Review Bot', pad=20, fontsize=14)
        plt.xlabel('Bot', fontsize=12)
        plt.ylabel('Ratio of Comments', fontsize=12)
        plt.legend(
            title='Category',
            bbox_to_anchor=(1.05, 1),
            loc='upper left',
            fontsize=10
        )
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Add percentage labels on bars
        for c in ax.containers:
            # Convert to percentages for labels
            ax.bar_label(c, fmt='%.1f%%', label_type='center')

        # Adjust layout to prevent label cutoff
        plt.tight_layout()

        # Save chart
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def create_bot_comparison_chart(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Create a radar chart comparing different aspects of bot performance"""
        # Prepare data
        bots = list(metrics.keys())
        metrics_list = ['critical_bug_ratio', 'nitpick_ratio', 'other_ratio']
        
        # Set up the radar chart
        angles = np.linspace(0, 2*np.pi, len(metrics_list), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Plot each bot
        for idx, bot in enumerate(bots):
            values = [metrics[bot][m] for m in metrics_list]
            values = np.concatenate((values, [values[0]]))  # complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, label=bot)
            ax.fill(angles, values, alpha=0.25)
        
        # Set the labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(['Critical Bugs', 'Nitpicks', 'Other'])
        
        plt.title('Bot Performance Comparison', pad=20, fontsize=14)
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def save_metrics_report(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Save detailed metrics report to file"""
        with open(output_file, 'w') as f:
            f.write("Code Review Bot Analysis Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Calculate overall statistics
            total_comments = sum(m['total_comments'] for m in metrics.values())
            total_critical = sum(m['critical_bug_ratio'] * m['total_comments'] for m in metrics.values())
            total_nitpicks = sum(m['nitpick_ratio'] * m['total_comments'] for m in metrics.values())
            total_other = sum(m['other_ratio'] * m['total_comments'] for m in metrics.values())

            # Write overall statistics
            f.write("Overall Statistics\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total Comments Analyzed: {total_comments}\n")
            f.write(f"Total Critical Bugs Found: {total_critical:.0f} ({(total_critical/total_comments)*100:.1f}%)\n")
            f.write(f"Total Nitpicks Made: {total_nitpicks:.0f} ({(total_nitpicks/total_comments)*100:.1f}%)\n")
            f.write(f"Total Other Comments: {total_other:.0f} ({(total_other/total_comments)*100:.1f}%)\n\n")

            # Write per-bot analysis
            f.write("Per-Bot Analysis\n")
            f.write("-" * 30 + "\n")
            
            for bot, scores in metrics.items():
                f.write(f"\nBot: {bot}\n")
                f.write("=" * (len(bot) + 5) + "\n")
                
                # Basic metrics
                f.write(f"Total Comments: {scores['total_comments']}\n\n")
                
                # Category breakdown
                f.write("Category Distribution:\n")
                f.write(f"- Critical Bugs: {scores['critical_bug_ratio']*100:.1f}% ")
                f.write(f"({int(scores['critical_bug_ratio'] * scores['total_comments'])} comments)\n")
                
                f.write(f"- Nitpicks: {scores['nitpick_ratio']*100:.1f}% ")
                f.write(f"({int(scores['nitpick_ratio'] * scores['total_comments'])} comments)\n")
                
                f.write(f"- Other Feedback: {scores['other_ratio']*100:.1f}% ")
                f.write(f"({int(scores['other_ratio'] * scores['total_comments'])} comments)\n\n")

    @staticmethod
    def create_trend_chart(metrics_over_time: List[Dict[str, Dict[str, float]]], timestamps: List[datetime], output_file: str):
        """Create a line chart showing how metrics change over time"""
        # Prepare data
        dates = [t.strftime('%Y-%m-%d') for t in timestamps]
        bots = list(metrics_over_time[0].keys())
        
        # Create separate dataframes for each metric
        critical_data = []
        nitpick_data = []
        other_data = []
        
        for date, metrics in zip(dates, metrics_over_time):
            for bot in bots:
                critical_data.append({
                    'Date': date,
                    'Bot': bot,
                    'Ratio': metrics[bot]['critical_bug_ratio']
                })
                nitpick_data.append({
                    'Date': date,
                    'Bot': bot,
                    'Ratio': metrics[bot]['nitpick_ratio']
                })
                other_data.append({
                    'Date': date,
                    'Bot': bot,
                    'Ratio': metrics[bot]['other_ratio']
                })

        # Create subplot for each metric
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
        
        # Plot Critical Bugs
        df_critical = pd.DataFrame(critical_data)
        sns.lineplot(data=df_critical, x='Date', y='Ratio', hue='Bot', ax=ax1)
        ax1.set_title('Critical Bug Ratio Over Time')
        ax1.set_ylabel('Ratio')
        
        # Plot Nitpicks
        df_nitpick = pd.DataFrame(nitpick_data)
        sns.lineplot(data=df_nitpick, x='Date', y='Ratio', hue='Bot', ax=ax2)
        ax2.set_title('Nitpick Ratio Over Time')
        ax2.set_ylabel('Ratio')
        
        # Plot Other
        df_other = pd.DataFrame(other_data)
        sns.lineplot(data=df_other, x='Date', y='Ratio', hue='Bot', ax=ax3)
        ax3.set_title('Other Comments Ratio Over Time')
        ax3.set_ylabel('Ratio')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def export_to_excel(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Export metrics to Excel file with multiple sheets"""
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Create summary sheet
            summary_data = []
            for bot, scores in metrics.items():
                summary_data.append({
                    'Bot': bot,
                    'Total Comments': scores['total_comments'],
                    'Critical Bug Ratio': f"{scores['critical_bug_ratio']*100:.1f}%",
                    'Nitpick Ratio': f"{scores['nitpick_ratio']*100:.1f}%",
                    'Other Ratio': f"{scores['other_ratio']*100:.1f}%"
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Create detailed metrics sheet
            detailed_data = []
            for bot, scores in metrics.items():
                detailed_data.append({
                    'Bot': bot,
                    'Total Comments': scores['total_comments'],
                    'Critical Bugs Count': int(scores['critical_bug_ratio'] * scores['total_comments']),
                    'Critical Bug Ratio': scores['critical_bug_ratio'],
                    'Nitpicks Count': int(scores['nitpick_ratio'] * scores['total_comments']),
                    'Nitpick Ratio': scores['nitpick_ratio'],
                    'Other Count': int(scores['other_ratio'] * scores['total_comments']),
                    'Other Ratio': scores['other_ratio']
                })
            
            df_detailed = pd.DataFrame(detailed_data)
            df_detailed.to_excel(writer, sheet_name='Detailed Metrics', index=False)

            