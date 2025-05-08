#!/bin/bash
echo "Deploying application..."
#!/bin/bash
echo "Building Docker images..."
docker-compose build

echo "Applying Kubernetes configs..."
kubectl apply -f k8s/kubernetes.yaml

echo "Running migrations and seeders..."
python3 core/analytics/advanced_trend_analytics.py
python3 core/viral/viral_scraper.py
python3 core/monetization/payment_engine.py

echo "Deployment complete."
