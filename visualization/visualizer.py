import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict

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

        plt.figure(figsize=(12, 6))
        ax = df.plot(
            x='Bot',
            y=['Critical Bugs', 'Nitpicks', 'Other'],
            kind='bar',
            stacked=True,
            color=['#ff6b6b', '#4ecdc4', '#45b7d1']
        )

        plt.title('Comment Category Distribution by Code Review Bot', pad=20, fontsize=14)
        plt.xlabel('Bot', fontsize=12)
        plt.ylabel('Ratio of Comments', fontsize=12)
        plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        plt.grid(axis='y', linestyle='--', alpha=0.7)

        # Add percentage labels
        for c in ax.containers:
            ax.bar_label(c, fmt='%.1f%%', label_type='center')

        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def create_bot_comparison_chart(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Create a radar chart comparing different aspects of bot performance"""
        bots = list(metrics.keys())
        metrics_list = ['critical_bug_ratio', 'nitpick_ratio', 'other_ratio']
        
        angles = np.linspace(0, 2*np.pi, len(metrics_list), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        for idx, bot in enumerate(bots):
            values = [metrics[bot][m] for m in metrics_list]
            values = np.concatenate((values, [values[0]]))
            
            ax.plot(angles, values, 'o-', linewidth=2, label=bot)
            ax.fill(angles, values, alpha=0.25)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(['Critical Bugs', 'Nitpicks', 'Other'])
        
        plt.title('Bot Performance Comparison', pad=20, fontsize=14)
        plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

    @staticmethod
    def save_metrics_report(metrics: Dict[str, Dict[str, float]], output_file: str):
        """Generate basic metrics report"""
        with open(output_file, 'w') as f:
            ResultsVisualizer._write_report_header(f)
            ResultsVisualizer._write_overall_stats(f, metrics)
            ResultsVisualizer._write_per_bot_analysis(f, metrics)
            ResultsVisualizer._write_summary_table(f, metrics)

    @staticmethod
    def save_detailed_report(analysis_results: Dict[str, Any], output_file: str):
        """Generate detailed report including per-comment analysis"""
        metrics = analysis_results['metrics']
        classifications = analysis_results['classifications']
        
        with open(output_file, 'w') as f:
            ResultsVisualizer._write_report_header(f)
            ResultsVisualizer._write_overall_stats(f, metrics)
            ResultsVisualizer._write_per_bot_analysis(f, metrics)
            ResultsVisualizer._write_detailed_classifications(f, classifications)
            ResultsVisualizer._write_summary_table(f, metrics)

    @staticmethod
    def _write_report_header(f):
        f.write("Code Review Bot Analysis Report\n")
        f.write("=" * 80 + "\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    @staticmethod
    def _write_overall_stats(f, metrics):
        total_comments = sum(m['total_comments'] for m in metrics.values())
        total_critical = sum(m['critical_bug_ratio'] * m['total_comments'] for m in metrics.values())
        total_nitpicks = sum(m['nitpick_ratio'] * m['total_comments'] for m in metrics.values())
        total_other = sum(m['other_ratio'] * m['total_comments'] for m in metrics.values())
        
        f.write("Overall Statistics\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Comments Analyzed: {total_comments}\n")
        f.write(f"Total Critical Bugs Found: {total_critical:.0f} ({total_critical/total_comments:.1%})\n")
        f.write(f"Total Nitpicks Made: {total_nitpicks:.0f} ({total_nitpicks/total_comments:.1%})\n")
        f.write(f"Total Other Comments: {total_other:.0f} ({total_other/total_comments:.1%})\n\n")

    @staticmethod
    def _write_per_bot_analysis(f, metrics):
        f.write("\nPer-Bot Analysis\n")
        f.write("=" * 80 + "\n")
        
        for bot, scores in metrics.items():
            f.write(f"\nBot: {bot}\n")
            f.write(f"{'-' * (len(bot) + 5)}\n")
            f.write(f"Total Comments: {scores['total_comments']}\n")
            f.write(f"Critical Bug Ratio: {scores['critical_bug_ratio']:.1%}\n")
            f.write(f"Nitpick Ratio: {scores['nitpick_ratio']:.1%}\n")
            f.write(f"Other Feedback Ratio: {scores['other_ratio']:.1%}\n")
            
            # Calculate raw numbers
            critical_count = int(scores['critical_bug_ratio'] * scores['total_comments'])
            nitpick_count = int(scores['nitpick_ratio'] * scores['total_comments'])
            other_count = int(scores['other_ratio'] * scores['total_comments'])
            
            f.write("\nRaw Numbers:\n")
            f.write(f"- Critical Bugs: {critical_count}\n")
            f.write(f"- Nitpicks: {nitpick_count}\n")
            f.write(f"- Other Comments: {other_count}\n\n")

    @staticmethod
    def _write_detailed_classifications(f, classifications):
        f.write("\nDetailed Classifications\n")
        f.write("=" * 80 + "\n")
        
        for bot_name, pr_data in classifications.items():
            f.write(f"\nBot: {bot_name}\n")
            f.write(f"{'-' * (len(bot_name) + 5)}\n")
            
            for pr_number, comments in pr_data.items():
                f.write(f"\nPR #{pr_number}\n")
                f.write("~" * 20 + "\n")
                
                # Group comments by category
                grouped_comments = defaultdict(list)
                for comment in comments:
                    grouped_comments[comment['category']].append(comment)
                
                for category in ['CRITICAL_BUG', 'NITPICK', 'OTHER']:
                    if category in grouped_comments:
                        f.write(f"\n{category} Comments:\n")
                        f.write("-" * 20 + "\n")
                        
                        for comment in grouped_comments[category]:
                            f.write(f"\nComment {comment['comment_index']} ")
                            f.write(f"(File: {comment['file_name']}, Lines: {comment['line_nums']})\n")
                            f.write("Comment: " + comment['comment'].strip() + "\n")
                            f.write("Code:\n" + comment['code_chunk'].strip() + "\n")
                            f.write("Reasoning: " + comment['reasoning'].strip() + "\n")
                            f.write("-" * 40 + "\n")
                    
                f.write("\n")

    @staticmethod
    def _write_summary_table(f, metrics):
        f.write("\nSummary Table\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'Bot Name':<20} {'Total':<10} {'Critical':<15} {'Nitpicks':<15} {'Other':<15}\n")
        f.write("-" * 80 + "\n")
        
        for bot, scores in metrics.items():
            total = scores['total_comments']
            critical = scores['critical_bug_ratio'] * total
            nitpicks = scores['nitpick_ratio'] * total
            other = scores['other_ratio'] * total
            
            f.write(f"{bot:<20} {total:<10d} {critical:>6.0f} ({scores['critical_bug_ratio']:>3.0%}) "
                f"{nitpicks:>6.0f} ({scores['nitpick_ratio']:>3.0%}) "
                f"{other:>6.0f} ({scores['other_ratio']:>3.0%})\n")

        f.write("\nNote: Percentages may not sum to 100% due to rounding\n")

