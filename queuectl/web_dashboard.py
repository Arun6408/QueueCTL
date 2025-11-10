"""Web dashboard for monitoring QueueCTL."""

from flask import Flask, jsonify, render_template_string
from queuectl.storage import Storage
from queuectl.worker import WorkerManager
from queuectl.metrics import Metrics


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>QueueCTL Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }
        .stat-card .value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        .stat-card.pending .value { color: #ff9800; }
        .stat-card.processing .value { color: #2196f3; }
        .stat-card.completed .value { color: #4caf50; }
        .stat-card.failed .value { color: #f44336; }
        .stat-card.dead .value { color: #9e9e9e; }
        .section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .section h2 {
            margin-top: 0;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #f9f9f9;
            font-weight: 600;
            color: #666;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge.pending { background: #fff3e0; color: #e65100; }
        .badge.processing { background: #e3f2fd; color: #1565c0; }
        .badge.completed { background: #e8f5e9; color: #2e7d32; }
        .badge.failed { background: #ffebee; color: #c62828; }
        .badge.dead { background: #f5f5f5; color: #616161; }
    </style>
</head>
<body>
    <div class="container">
        <h1>QueueCTL Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card pending">
                <h3>Pending</h3>
                <div class="value" id="pending">0</div>
            </div>
            <div class="stat-card processing">
                <h3>Processing</h3>
                <div class="value" id="processing">0</div>
            </div>
            <div class="stat-card completed">
                <h3>Completed</h3>
                <div class="value" id="completed">0</div>
            </div>
            <div class="stat-card failed">
                <h3>Failed</h3>
                <div class="value" id="failed">0</div>
            </div>
            <div class="stat-card dead">
                <h3>Dead Letter Queue</h3>
                <div class="value" id="dead">0</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Workers</h2>
            <div id="workers">Loading...</div>
        </div>
        
        <div class="section">
            <h2>Recent Jobs</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Command</th>
                        <th>State</th>
                        <th>Attempts</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody id="jobs">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                const [statsRes, workersRes, jobsRes] = await Promise.all([
                    fetch('/api/stats'),
                    fetch('/api/workers'),
                    fetch('/api/jobs?limit=20')
                ]);
                
                const stats = await statsRes.json();
                const workers = await workersRes.json();
                const jobs = await jobsRes.json();
                
                // Update stats
                document.getElementById('pending').textContent = stats.pending || 0;
                document.getElementById('processing').textContent = stats.processing || 0;
                document.getElementById('completed').textContent = stats.completed || 0;
                document.getElementById('failed').textContent = stats.failed || 0;
                document.getElementById('dead').textContent = stats.dead || 0;
                
                // Update workers
                const workersHtml = workers.length > 0 
                    ? workers.map(w => `
                        <div style="padding: 10px; border-bottom: 1px solid #eee;">
                            <strong>Worker ${w.id}</strong> - 
                            ${w.running ? '<span style="color: green;">Running</span>' : '<span style="color: red;">Stopped</span>'}
                            ${w.current_job ? ` (Processing: ${w.current_job})` : ''}
                        </div>
                    `).join('')
                    : '<p>No active workers</p>';
                document.getElementById('workers').innerHTML = workersHtml;
                
                // Update jobs
                const jobsHtml = jobs.length > 0
                    ? jobs.map(job => `
                        <tr>
                            <td>${job.id}</td>
                            <td><code>${job.command}</code></td>
                            <td><span class="badge ${job.state}">${job.state}</span></td>
                            <td>${job.attempts}/${job.max_retries}</td>
                            <td>${new Date(job.created_at).toLocaleString()}</td>
                        </tr>
                    `).join('')
                    : '<tr><td colspan="5">No jobs</td></tr>';
                document.getElementById('jobs').innerHTML = jobsHtml;
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        loadData();
        setInterval(loadData, 5000);
    </script>
</body>
</html>
"""


def create_app(storage: Storage, worker_manager: WorkerManager, metrics: Metrics):
    """Create Flask app for dashboard."""
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return render_template_string(DASHBOARD_HTML)
    
    @app.route('/api/stats')
    def api_stats():
        stats = storage.get_stats()
        exec_stats = metrics.get_execution_stats()
        return jsonify({
            **stats,
            "execution_stats": exec_stats,
        })
    
    @app.route('/api/workers')
    def api_workers():
        return jsonify(worker_manager.get_worker_status())
    
    @app.route('/api/jobs')
    def api_jobs():
        from flask import request
        limit = request.args.get('limit', 20, type=int)
        state = request.args.get('state', type=str)
        jobs = storage.list_jobs(state=state, limit=limit)
        return jsonify([job.to_dict() for job in jobs])
    
    return app


def start_dashboard(storage: Storage, worker_manager: WorkerManager, metrics: Metrics, port: int = 8080):
    """Start the web dashboard server."""
    app = create_app(storage, worker_manager, metrics)
    app.run(host='0.0.0.0', port=port, debug=False)

