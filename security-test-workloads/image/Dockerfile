# Intentionally weak image for Trivy image/filesystem scans (EOL base + old deps).
# Build: docker build -f Dockerfile -t security-test-bench/vulnerable-app:test .
FROM python:3.6-slim-stretch

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Run as root, no USER directive (common misconfiguration signal)
CMD ["python", "-c", "import http.server; http.server.HTTPServer(('0.0.0.0', 8080), http.server.SimpleHTTPRequestHandler).serve_forever()"]
