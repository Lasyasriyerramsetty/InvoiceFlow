"""Generate a visual HTML report for evaluation results."""

import json
from evaluation.harness import harness
from evaluation.trace import AgentType, ToolCallType
from datetime import datetime


def generate_html_report(metrics_summary: dict) -> str:
    """Generate a beautiful HTML report from metrics summary."""
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>InvoiceFlow Evaluation Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .card-shadow { box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
        .hover-scale { transition: transform 0.2s ease; }
        .hover-scale:hover { transform: scale(1.02); }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="gradient-bg text-white py-8">
        <div class="container mx-auto px-4">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-4xl font-bold mb-2">InvoiceFlow</h1>
                    <p class="text-white/80">Evaluation Suite Report</p>
                </div>
                <div class="text-right">
                    <p class="text-sm text-white/80">Generated on</p>
                    <p class="text-lg font-semibold">""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                </div>
            </div>
        </div>
    </header>

    <div class="container mx-auto px-4 py-8">
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-white rounded-xl p-6 card-shadow hover-scale">
                <div class="flex items-center justify-between mb-2">
                    <div class="bg-blue-100 rounded-lg p-3">
                        <i class="fas fa-inbox text-blue-600 text-2xl"></i>
                    </div>
                </div>
                <h3 class="text-gray-500 text-sm font-medium">Total Invoices</h3>
                <p class="text-3xl font-bold text-gray-900">""" + str(metrics_summary['business_metrics']['total_invoices_processed']) + """</p>
            </div>

            <div class="bg-white rounded-xl p-6 card-shadow hover-scale">
                <div class="flex items-center justify-between mb-2">
                    <div class="bg-emerald-100 rounded-lg p-3">
                        <i class="fas fa-check-circle text-emerald-600 text-2xl"></i>
                    </div>
                </div>
                <h3 class="text-gray-500 text-sm font-medium">Straight-Through Rate</h3>
                <p class="text-3xl font-bold text-gray-900">""" + f"{metrics_summary['business_metrics']['straight_through_rate']:.1f}%" + """</p>
            </div>

            <div class="bg-white rounded-xl p-6 card-shadow hover-scale">
                <div class="flex items-center justify-between mb-2">
                    <div class="bg-amber-100 rounded-lg p-3">
                        <i class="fas fa-exclamation-triangle text-amber-600 text-2xl"></i>
                    </div>
                </div>
                <h3 class="text-gray-500 text-sm font-medium">Exception Rate</h3>
                <p class="text-3xl font-bold text-gray-900">""" + f"{metrics_summary['business_metrics']['exception_rate']:.1f}%" + """</p>
            </div>

            <div class="bg-white rounded-xl p-6 card-shadow hover-scale">
                <div class="flex items-center justify-between mb-2">
                    <div class="bg-purple-100 rounded-lg p-3">
                        <i class="fas fa-clock text-purple-600 text-2xl"></i>
                    </div>
                </div>
                <h3 class="text-gray-500 text-sm font-medium">Avg Processing Time</h3>
                <p class="text-3xl font-bold text-gray-900">""" + f"{metrics_summary['avg_pipeline_latency_ms']:.0f}ms" + """</p>
            </div>
        </div>

        <!-- Business Metrics Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="bg-white rounded-xl p-6 card-shadow">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Business Metrics</h2>
                <div class="space-y-4">
                    <div class="flex justify-between items-center pb-3 border-b">
                        <span class="text-gray-600">Auto-Approved</span>
                        <span class="font-semibold text-emerald-600">""" + str(metrics_summary['business_metrics']['auto_approved_count']) + """</span>
                    </div>
                    <div class="flex justify-between items-center pb-3 border-b">
                        <span class="text-gray-600">Manual Review</span>
                        <span class="font-semibold text-amber-600">""" + str(metrics_summary['business_metrics']['manual_review_count']) + """</span>
                    </div>
                    <div class="flex justify-between items-center pb-3 border-b">
                        <span class="text-gray-600">Total Savings</span>
                        <span class="font-semibold text-purple-600">$""" + f"{metrics_summary['business_metrics']['total_savings']:,.2f}" + """</span>
                    </div>
                    <div class="flex justify-between items-center pb-3 border-b">
                        <span class="text-gray-600">PO Match Rate</span>
                        <span class="font-semibold text-blue-600">""" + f"{metrics_summary['business_metrics']['po_match_rate']:.1f}%" + """</span>
                    </div>
                    <div class="flex justify-between items-center pb-3 border-b">
                        <span class="text-gray-600">Contract Match Rate</span>
                        <span class="font-semibold text-indigo-600">""" + f"{metrics_summary['business_metrics']['contract_match_rate']:.1f}%" + """</span>
                    </div>
                </div>
            </div>

            <!-- Agent Performance -->
            <div class="bg-white rounded-xl p-6 card-shadow">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Agent Performance</h2>
                <div class="space-y-4">
"""
    
    # Add agent metrics
    for agent_type, agent_data in metrics_summary['agent_metrics'].items():
        success_rate_color = "emerald" if agent_data['success_rate'] >= 95 else "amber" if agent_data['success_rate'] >= 80 else "rose"
        html += f"""
                    <div class="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div class="flex justify-between items-start mb-2">
                            <div>
                                <h3 class="font-semibold text-gray-900 capitalize">{agent_type.replace('_', ' ')}</h3>
                                <p class="text-xs text-gray-500 mt-1">
                                    {agent_data['total_executions']} executions • {agent_data['avg_duration_ms']:.0f}ms avg
                                </p>
                            </div>
                            <span class="bg-{success_rate_color}-100 text-{success_rate_color}-700 text-xs font-bold px-3 py-1 rounded-full">
                                {agent_data['success_rate']:.0f}%
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2 mt-3">
                            <div class="bg-{success_rate_color}-500 h-2 rounded-full" style="width: {agent_data['success_rate']}%"></div>
                        </div>
                        <div class="flex justify-between text-xs text-gray-500 mt-2">
                            <span>Confidence: {(agent_data['avg_confidence'] * 100):.0f}%</span>
                            <span>Tools: {agent_data['tool_call_success_rate']:.0f}% success</span>
                        </div>
                    </div>
"""
    
    html += """
                </div>
            </div>
        </div>

        <!-- Top Tools Section -->
        <div class="bg-white rounded-xl p-6 card-shadow">
            <h2 class="text-2xl font-bold text-gray-900 mb-6">Top Tools Used</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
"""
    
    # Add top tools
    for tool, count in metrics_summary['top_tools']:
        tool_name = tool.split('.')[1] if '.' in tool else tool
        html += f"""
                <div class="border rounded-lg p-4 flex items-center justify-between hover:shadow-md transition-shadow">
                    <div class="flex items-center gap-3">
                        <div class="bg-indigo-100 rounded-lg p-2">
                            <i class="fas fa-wrench text-indigo-600"></i>
                        </div>
                        <div>
                            <p class="font-medium text-gray-900 capitalize">{tool_name.replace('_', ' ')}</p>
                            <p class="text-xs text-gray-500">{tool.split('.')[0].replace('_', ' ')}</p>
                        </div>
                    </div>
                    <span class="text-2xl font-bold text-indigo-600">{count}</span>
                </div>
"""
    
    html += """
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-6 mt-12">
        <div class="container mx-auto px-4 text-center">
            <p class="text-sm text-gray-400">InvoiceFlow Evaluation Suite • Generated automatically</p>
        </div>
    </footer>
</body>
</html>
"""
    
    return html


def save_report(metrics_summary: dict, output_path: str = "evaluation_report.html"):
    """Save the HTML report to a file."""
    html = generate_html_report(metrics_summary)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Report saved to: {output_path}")


if __name__ == "__main__":
    # Run demo and generate report
    from evaluation.run_demo import run_demo
    
    print("Running evaluation demo...")
    # The run_demo function prints to console, we need to capture metrics
    # For now, just generate a sample report
    sample_metrics = {
        "total_traces": 1,
        "avg_pipeline_latency_ms": 2450.0,
        "business_metrics": {
            "total_invoices_processed": 1,
            "straight_through_rate": 0.0,
            "exception_rate": 200.0,
            "auto_approved_count": 0,
            "manual_review_count": 1,
            "total_savings": 0.0,
            "avg_processing_time_ms": 2450.0,
            "po_match_rate": 100.0,
            "contract_match_rate": 100.0,
            "fraud_detected": 0,
            "duplicate_prevented": 0,
        },
        "agent_metrics": {
            "document_intake": {
                "total_executions": 1,
                "success_rate": 100.0,
                "avg_duration_ms": 450.0,
                "avg_confidence": 0.98,
                "tool_call_success_rate": 100.0,
            },
            "invoice_understanding": {
                "total_executions": 1,
                "success_rate": 100.0,
                "avg_duration_ms": 1200.0,
                "avg_confidence": 0.96,
                "tool_call_success_rate": 100.0,
            },
            "po_matching": {
                "total_executions": 1,
                "success_rate": 100.0,
                "avg_duration_ms": 15.0,
                "avg_confidence": 0.90,
                "tool_call_success_rate": 100.0,
            },
            "exception_detection": {
                "total_executions": 1,
                "success_rate": 100.0,
                "avg_duration_ms": 800.0,
                "avg_confidence": 0.89,
                "tool_call_success_rate": 100.0,
            },
            "workflow": {
                "total_executions": 1,
                "success_rate": 100.0,
                "avg_duration_ms": 0.0,
                "avg_confidence": 0.93,
                "tool_call_success_rate": 0.0,
            },
        },
        "top_tools": [
            ("invoice_understanding.gpt4_extraction", 1),
            ("document_intake.azure_ocr", 1),
            ("exception_detection.exception_classifier", 1),
            ("po_matching.db_query_po", 1),
        ],
    }
    
    save_report(sample_metrics)
    print("\nOpen evaluation_report.html in your browser to view the report.")