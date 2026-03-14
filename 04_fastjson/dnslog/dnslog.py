import datetime
import threading
from flask import Flask, jsonify, make_response, render_template_string, request
from dnslib import DNSRecord, QTYPE, RR, A
from dnslib.server import DNSServer, BaseResolver, DNSLogger

app = Flask(__name__)

# In-memory storage for DNS query logs
# Each entry: {'time': str, 'client_ip': str, 'query': str}
dns_logs = []

class CustomResolver(BaseResolver):
    def resolve(self, request, handler):
        qname = str(request.q.qname)
        client_ip = handler.client_address[0]
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if the query is for our target domain
        if qname.endswith("log.rcs-team.com.") or qname == "log.rcs-team.com.":
            # Add to logs
            dns_logs.append({
                'time': current_time,
                'client_ip': client_ip,
                'query': qname.rstrip('.')
            })
            # Keep only the last 1000 logs to prevent memory leak
            if len(dns_logs) > 1000:
                dns_logs.pop(0)

        # Build dummy response pointing to 127.0.0.1
        reply = request.reply()
        if request.q.qtype == QTYPE.A:
            reply.add_answer(RR(qname, QTYPE.A, rdata=A("127.0.0.1"), ttl=60))
        return reply

def start_dns_server():
    resolver = CustomResolver()
    logger = DNSLogger(log="request,reply,truncated,error")
    # Listen on all interfaces on port 53 (UDP)
    server = DNSServer(resolver, port=53, address="0.0.0.0", logger=logger)
    print("Starting DNS server on port 53...")
    server.start_thread()

# HTML template for the Flask web page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="3">
    <title>DNSLog Server</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
        th { background-color: #f4f4f4; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>DNSLog Server Records</h1>
    <p>Target domain: <b>log.rcs-team.com</b></p>
    <table>
        <thead>
            <tr>
                <th>Time</th>
                <th>Client IP</th>
                <th>Query</th>
            </tr>
        </thead>
        <tbody>
            {% for log in logs|reverse %}
            <tr>
                <td>{{ log.time }}</td>
                <td>{{ log.client_ip }}</td>
                <td>{{ log.query }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" style="text-align: center;">No queries recorded yet.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    resp = make_response(render_template_string(HTML_TEMPLATE, logs=dns_logs))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '-1'
    return resp


@app.route('/api/logs')
def api_logs():
    query = request.args.get('query', '').strip().lower()
    if query:
        logs = [log for log in dns_logs if query in log['query'].lower()]
    else:
        logs = list(dns_logs)
    return jsonify({'count': len(logs), 'logs': logs})

if __name__ == '__main__':
    # Start the DNS server in a separate thread
    dns_thread = threading.Thread(target=start_dns_server, daemon=True)
    dns_thread.start()
    
    # Start the Flask web server
    print("Starting Web UI on port 80...")
    app.run(host='0.0.0.0', port=80)
