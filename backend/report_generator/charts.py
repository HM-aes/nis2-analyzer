"""
Chart generation module for NIS2 PDF reports.
Uses Plotly with kaleido for PNG export.
All functions return PNG bytes suitable for embedding in ReportLab PDFs.
"""

import io
import plotly.graph_objects as go
from reportlab.lib.utils import ImageReader


def compliance_gauge_image(score: int, sector_avg: int = None) -> bytes:
    """
    Generate compliance score gauge as PNG bytes.
    score: 0-100
    sector_avg: optional sector benchmark line
    """
    color = '#22c55e' if score >= 70 else \
            '#f59e0b' if score >= 40 else '#ef4444'

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Compliance Score", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40], 'color': '#fee2e2'},
                {'range': [40, 70], 'color': '#fef3c7'},
                {'range': [70, 100], 'color': '#dcfce7'},
            ],
            'threshold': {
                'line': {'color': '#1d4ed8', 'width': 4},
                'thickness': 0.75,
                'value': sector_avg or score,
            }
        }
    ))
    fig.update_layout(
        width=500, height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='white',
    )
    return fig.to_image(format='png')


def severity_bar_chart_image(
        critical: int, high: int,
        medium: int, low: int) -> bytes:
    """
    Generate severity breakdown bar chart as PNG bytes.
    """
    fig = go.Figure(go.Bar(
        x=['Critical', 'High', 'Medium', 'Low'],
        y=[critical, high, medium, low],
        marker_color=['#dc2626', '#ea580c', '#ca8a04', '#16a34a'],
        text=[critical, high, medium, low],
        textposition='outside',
    ))
    fig.update_layout(
        title='Gap Severity Distribution',
        width=600, height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        yaxis_title='Number of Gaps',
        showlegend=False,
    )
    return fig.to_image(format='png')


def category_heatmap_image(category_data: dict) -> bytes:
    """
    Generate category heatmap as PNG bytes.
    category_data: {'Access Control': 3, 'Incident Response': 5}
    """
    if not category_data:
        # Return a minimal blank chart if no data
        category_data = {'No Data': 0}

    categories = list(category_data.keys())
    values = list(category_data.values())

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker_color=[
            '#dc2626' if v >= 5 else
            '#ea580c' if v >= 3 else
            '#ca8a04' if v >= 1 else '#16a34a'
            for v in values
        ],
        text=values,
        textposition='outside',
    ))
    fig.update_layout(
        title='Gaps by NIS2 Category',
        width=700, height=max(300, len(categories) * 40 + 100),
        margin=dict(l=180, r=50, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis_title='Number of Gaps',
    )
    return fig.to_image(format='png')


def remediation_timeline_image(phases: list) -> bytes:
    """
    Generate remediation timeline Gantt chart.
    phases: [{'name': 'Phase 1', 'start': 0, 'end': 30, 'tasks': 5}]
    """
    fig = go.Figure()
    colors = ['#dc2626', '#ea580c', '#ca8a04']

    for i, phase in enumerate(phases):
        fig.add_trace(go.Bar(
            name=phase['name'],
            x=[phase['end'] - phase['start']],
            y=[phase['name']],
            base=[phase['start']],
            orientation='h',
            marker_color=colors[i % len(colors)],
            text=f"{phase['tasks']} gaps",
            textposition='inside',
        ))

    fig.update_layout(
        title='Remediation Timeline (Days)',
        width=700, height=300,
        barmode='stack',
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis_title='Days from Start',
        margin=dict(l=150, r=50, t=50, b=20),
    )
    return fig.to_image(format='png')


def png_to_reportlab_image(png_bytes: bytes, width: float, height: float):
    """Convert PNG bytes to ReportLab ImageReader."""
    return ImageReader(io.BytesIO(png_bytes))
