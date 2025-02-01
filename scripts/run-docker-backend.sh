docker build -t gcr.io/budgetapp-449511/backend ../../backend
docker run -d -p 8000:8000 gcr.io/budgetapp-449511/backend