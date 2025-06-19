# Deploying FastAPI + Celery + Redis to Google Cloud Platform (GCP)

This guide walks you through deploying your containerized FastAPI API, Celery worker, and Redis (Memorystore) stack to GCP using **Cloud Run** and **Memorystore** for a scalable, low-latency, production-ready setup.

---

## Prerequisites
- Google Cloud account with billing enabled and **sufficient credits**
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Docker installed
- Project code is containerized (Dockerfile ready)
- You have access to the Google Cloud Console

---

## 1. Set Up Your GCP Project & Enable APIs

```sh
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com redis.googleapis.com
```

---

## 2. Create Artifact Registry for Docker Images

```sh
gcloud artifacts repositories create storymimi-repo --repository-format=docker --location=us-central1
```

---

## 3. Build & Push Docker Images

```sh
# Set variables
REGION=us-central1
PROJECT_ID=$(gcloud config get-value project)
REPO=storymimi-repo

# Build and tag images
# API
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:latest -f Dockerfile .
# Worker (same image, different entrypoint)
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/worker:latest -f Dockerfile .

# Authenticate Docker to Artifact Registry
gcloud auth configure-docker $REGION-docker.pkg.dev

# Push images
# API
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:latest
# Worker
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/worker:latest
```

---

## 4. Provision Memorystore (Redis)

```sh
gcloud redis instances create storymimi-redis \
  --size=1 --region=us-central1 --zone=us-central1-a --redis-version=redis_7_0 --tier=basic

gcloud redis instances describe storymimi-redis --region=us-central1
# Note the host IP (e.g., 10.0.0.3) and port (default 6379)
```

---

## 5. Configure VPC Connector (for Cloud Run to access Memorystore)

```sh
gcloud compute networks vpc-access connectors create storymimi-connector \
  --region=us-central1 --network=default --range=10.8.0.0/28
```

---

## 6. Set Up Environment Variables

- Copy `.env.example` to `.env`
- Set `REDIS_URL` to use the internal IP of your Memorystore instance:
  ```
  REDIS_URL=redis://<MEMORYSTORE_IP>:6379/0
  ```
- Set all other secrets and API keys as needed

---

## 7. Deploy FastAPI API to Cloud Run

```sh
gcloud run deploy storymimi-api \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/api:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars=REDIS_URL=redis://<MEMORYSTORE_IP>:6379/0,... \
  --vpc-connector=storymimi-connector \
  --memory=1Gi --cpu=1 \
  --min-instances=1 --max-instances=5
```
- Add all required env vars with `--set-env-vars` or use a `.env.yaml` file.
- For private APIs, remove `--allow-unauthenticated` and set up IAM.

---

## 8. Deploy Celery Worker to Cloud Run

```sh
gcloud run deploy storymimi-worker \
  --image=$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/worker:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --set-env-vars=REDIS_URL=redis://<MEMORYSTORE_IP>:6379/0,... \
  --vpc-connector=storymimi-connector \
  --memory=1Gi --cpu=1 \
  --min-instances=1 --max-instances=5 \
  --command="celery" --args="-A app.core.celery_app:celery_app worker --loglevel=info"
```
- The worker service does not need to be public.
- You may want to use a custom entrypoint/command if needed.

---

## 9. Service Accounts & Permissions

- Create a service account for Cloud Run with access to:
  - Memorystore (VPC access)
  - Google LLM APIs (if using Gemini, etc.)
- Assign the service account to both Cloud Run services:
  ```sh
  gcloud run services update storymimi-api --service-account=YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com --region=$REGION
  gcloud run services update storymimi-worker --service-account=YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com --region=$REGION
  ```
- Use Workload Identity Federation for secure, keyless access to Google APIs.

---

## 10. Best Practices
- Deploy in the same region as your LLM endpoints (e.g., us-central1 for Gemini)
- Use managed Redis (Memorystore) in the same region/VPC
- Set min instances > 0 on Cloud Run for low latency
- Use Google service accounts for authentication to Google APIs
- Enable Cloud Monitoring and Logging
- Use HTTPS endpoints

---

## 11. Testing & Monitoring
- Visit your Cloud Run API URL (see `gcloud run services list`)
- Use `/health` endpoint for readiness/liveness checks
- Monitor logs in Cloud Console (Cloud Run, Logging)
- Monitor Redis metrics in Memorystore

---

## 12. Cleanup (to avoid charges)

```sh
gcloud run services delete storymimi-api --region=$REGION
gcloud run services delete storymimi-worker --region=$REGION
gcloud redis instances delete storymimi-redis --region=$REGION
gcloud artifacts repositories delete storymimi-repo --location=$REGION
```

---

## References
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Memorystore Docs](https://cloud.google.com/memorystore/docs/redis)
- [Artifact Registry Docs](https://cloud.google.com/artifact-registry/docs/docker/quickstart)
- [Cloud Run VPC Access](https://cloud.google.com/run/docs/configuring/connecting-vpc)
- [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)

---

**You are now ready to deploy your FastAPI + Celery + Redis stack to GCP!**
If you need a GKE (Kubernetes) version or have any questions, just ask! 