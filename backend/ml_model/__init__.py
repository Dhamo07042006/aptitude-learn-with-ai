"""
ml_model package initializer.
Expose report generator and visualization functions.
"""

from .report_generator import generate_report
from .visualization import (
    plot_accuracy,
    plot_topic_performance,
    plot_subtopic_performance,
)

__all__ = [
    "generate_report",
    "plot_accuracy",
    "plot_topic_performance",
    "plot_subtopic_performance",
]
