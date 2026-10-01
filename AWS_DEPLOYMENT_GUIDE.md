# AWS Deployment Guide — Global Rails

> Financial SDK for Autonomous AI Agents | Python (FastAPI/MCP) + React Frontend
> Current stack: Vercel (frontend + backend serverless) → migrating to AWS for scale

---

## 1. Why AWS for Global Rails

| Need | AWS Fit |
|---|---|
| Persistent WebSocket / MCP server | ECS Fargate (Vercel can't hold long-lived connections) |
| Low-latency M-Pesa / crypto callbacks | API Gateway + Lambda in `af-south-1` (Cape Town) |
| Agent state & session storage | ElastiCache (Redis) |
| Wallet keys & API secrets vault | AWS Secrets Manager |
| Blockchain RPC call caching | DynamoDB (sub-ms reads) |
| Cost credits for a startup | AWS Activate program (see §6) |

---

## 2. Recommended AWS Services

### 2.1 Compute

| Service | Use case | Why |
|---|---|---|
| **ECS Fargate** | FastAPI + MCP server (`backend/`) | Serverless containers — no EC2 management; scales to zero when idle |
| **AWS Lambda** | Lightweight REST handlers (`rest_handlers.py`), webhooks from M-Pesa/Kotani | Pay-per-invocation; perfect for sporadic payment callbacks |
| **API Gateway (HTTP API)** | Public-facing `/api/*` routes, L402 paywall endpoints | Handles auth, throttling, CORS in one place |
| **CloudFront + S3** | React frontend (`frontend/`) | Replace Vercel; globally cached static assets; ~$0.01/GB transfer |

### 2.2 Databases

| Service | Use case | Tier to start |
|---|---|---|
| **Amazon RDS (PostgreSQL)** | Agent transaction ledger, user accounts, payment history | `db.t4g.micro` — Free Tier eligible (750 hrs/month for 12 months) |
| **Amazon DynamoDB** | Real-time exchange rate cache, wallet config lookups, MCP tool state | On-Demand billing; Free Tier: 25 GB + 2.5M requests/month |
| **Amazon ElastiCache (Redis Serverless)** | Agent session memory, rate-limit counters, swap quote TTL | Serverless tier starts at ~$0.125/GB-hr; no minimum |
| **Amazon S3** | SDK artefacts, audit logs, off-ramp receipts | 5 GB free; then ~$0.023/GB |

**Decision rule:**
- Structured relational data (users, transactions) → **RDS Postgres**
- High-frequency key-value reads (rates, wallet state) → **DynamoDB**
- Ephemeral / TTL data (agent sessions, caches) → **ElastiCache Redis**

### 2.3 Authentication & Identity

| Service | Role |
|---|---|
| **Amazon Cognito User Pools** | Dashboard login (agent operators), JWT issuance, MFA |
| **Amazon Cognito Identity Pools** | Federated access — let agents assume IAM roles for scoped AWS resource access |
| **AWS IAM Roles** | Per-service least-privilege (ECS task role, Lambda execution role) |
| **AWS Secrets Manager** | Store `MPESA_CONSUMER_KEY`, `KOTANI_API_KEY`, `GROQ_API_KEY`, wallet private keys |

> **Cognito Free Tier:** 50,000 monthly active users (MAUs) free — more than sufficient for early traction.

### 2.4 Observability & Security

| Service | Purpose |
|---|---|
| **AWS CloudWatch** | Logs, metrics, alarms for API latency and error rates |
| **AWS X-Ray** | Distributed tracing across Lambda → ECS → DynamoDB |
| **AWS WAF** | Protect API Gateway from abuse / rate-limit L402 endpoints |
| **AWS KMS** | Encrypt RDS at rest, Secrets Manager keys |

---

## 3. Recommended Architecture

```
Internet
    │
    ▼
CloudFront (CDN)
    ├── /static/* → S3 (React build)
    └── /api/*   → API Gateway (HTTP API)
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
         Lambda                ECS Fargate
    (webhooks, off-ramp     (FastAPI + MCP server,
     callbacks, light        long-lived agent sessions)
     REST handlers)                │
              │                    │
              └─────────┬──────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      RDS Postgres   DynamoDB   ElastiCache
    (transactions)  (rates/     (agent state/
                   wallet cfg)   sessions)
                        │
                  Secrets Manager
               (API keys, wallet keys)
```

---

## 4. Cost Estimate (Early-Stage / MVP)

> Based on moderate traffic: ~10K API calls/day, 2 agents running concurrently.

| Service | Free Tier | Est. Monthly Cost (post-free) |
|---|---|---|
| ECS Fargate (0.25 vCPU / 0.5 GB, 1 task) | — | ~$9/month |
| Lambda (10K invocations/day) | 1M req free | ~$0 in free tier |
| API Gateway | 1M calls/month free | ~$0 in free tier |
| RDS Postgres `db.t4g.micro` | 750 hrs/month (12 mo) | ~$0 yr 1; ~$13/mo after |
| DynamoDB On-Demand | 25 GB + 2.5M req free | ~$0 early stage |
| ElastiCache Redis Serverless | — | ~$5–15/month |
| S3 + CloudFront | 5 GB / 1 TB transfer free | ~$1–3/month |
| Secrets Manager | 30-day trial per secret | ~$0.40/secret/month |
| Cognito | 50K MAUs free | ~$0 early stage |
| **Estimated Total** | | **~$15–40/month** |

With **AWS Activate credits** (§6), year 1 is effectively **$0**.

---

## 5. Migration Path from Vercel

```
Phase 1 — Infra Bootstrap (Week 1–2)
  [ ] Create AWS account + enable MFA on root
  [ ] Set up IAM admin user (never use root for daily work)
  [ ] Configure AWS CLI locally: aws configure
  [ ] Create VPC with public + private subnets (use VPC Wizard)
  [ ] Store all secrets in Secrets Manager

Phase 2 — Database Layer (Week 2–3)
  [ ] Provision RDS Postgres (private subnet, encrypted)
  [ ] Set up DynamoDB tables: ExchangeRates, WalletConfig, AgentSessions
  [ ] Create ElastiCache Redis Serverless cluster

Phase 3 — Compute Migration (Week 3–4)
  [ ] Containerize backend/ → write Dockerfile
  [ ] Push image to Amazon ECR (Elastic Container Registry)
  [ ] Deploy ECS Fargate service with task role (least-privilege IAM)
  [ ] Wire API Gateway → ECS via Application Load Balancer (ALB)

Phase 4 — Frontend + Auth (Week 4–5)
  [ ] Build React app → upload to S3
  [ ] Set up CloudFront distribution pointing to S3 + API Gateway
  [ ] Configure Cognito User Pool for agent dashboard login
  [ ] Replace hardcoded env vars with Secrets Manager SDK calls

Phase 5 — Observability (Week 5–6)
  [ ] Enable CloudWatch Container Insights on ECS
  [ ] Set up X-Ray tracing on Lambda + FastAPI (aws-xray-sdk-python)
  [ ] Create CloudWatch alarms: error rate > 1%, p99 latency > 2s
```

---

## 6. Applying for AWS Credits (AWS Activate)

### 6.1 AWS Activate Founders (Self-Apply — No VC Required)

- **URL:** https://aws.amazon.com/activate/
- **Credits:** Up to **$1,000 USD** in AWS credits
- **Requirements:** Active AWS account; startup at idea/MVP stage
- **How to apply:**
  1. Go to the Activate portal and click **"Apply for Founders"**
  2. Describe your project — use the template below

### 6.2 AWS Activate Portfolio (Requires Accelerator/VC Affiliation)

- **Credits:** $5,000 – $100,000 USD depending on the organisation
- **Who qualifies:** Companies backed by AWS-affiliated VCs, incubators, or accelerators
- **Examples of qualifying orgs:** Y Combinator, Techstars, Google for Startups, MEST Africa, Founders Factory Africa

### 6.3 Credit Application Template

Use this when prompted to describe your company/project:

```
Company Name: Global Rails (African Rails)

One-line description:
A developer-first Python SDK giving autonomous AI agents native financial
capabilities across Africa — enabling programmatic M-Pesa payouts,
on-chain token swaps, and L402 micropayments without human-in-the-loop KYB.

Technical stack:
- Backend: Python (FastAPI, MCP server), deployed on AWS ECS Fargate
- Frontend: React, served via CloudFront + S3
- Databases: RDS PostgreSQL (transaction ledger), DynamoDB (rate cache),
  ElastiCache Redis (agent session state)
- Auth: Amazon Cognito
- Security: AWS Secrets Manager, KMS, WAF

AWS services we plan to use:
ECS Fargate, Lambda, API Gateway, RDS, DynamoDB, ElastiCache,
S3, CloudFront, Cognito, Secrets Manager, CloudWatch, X-Ray, KMS

Why we need credits:
We are an early-stage startup building financial infrastructure for AI
agents operating in African markets. AWS credits will allow us to stand
up production-grade infrastructure, run reliability tests against live
payment rails, and scale without upfront capital commitments during our
seed stage.

Stage: MVP / Pre-seed
Monthly AWS spend (projected): $40–200/month scaling to $500–2,000/month
at Series A
```

### 6.4 Additional Credit Sources

| Program | Credits | Link |
|---|---|---|
| **Google for Startups** | Up to $200K GCP credits | cloud.google.com/startup |
| **Microsoft for Startups** | Up to $150K Azure credits | microsoft.com/startups |
| **Stripe Atlas** | Various partner credits | stripe.com/atlas |
| **NVIDIA Inception** | GPU credits for AI workloads | nvidia.com/inception |

---

## 7. Key Environment Variables to Migrate to Secrets Manager

```bash
# Payment Rails
MPESA_CONSUMER_KEY
MPESA_CONSUMER_SECRET
MPESA_SHORTCODE
MPESA_PASSKEY
KOTANI_API_KEY
HONEYCOIN_API_KEY

# AI / LLM
GROQ_API_KEY
ANTHROPIC_API_KEY   # if added later

# Blockchain
PRIVATE_KEY         # wallet signing key — treat as highest-sensitivity
RPC_URL

# Database (auto-rotated by Secrets Manager)
DATABASE_URL
REDIS_URL
```

> Never commit these to git. Use `aws secretsmanager get-secret-value` in your ECS task definition.

---

## 8. Quick-Start Commands

```bash
# Install AWS CLI
pip install awscli && aws configure

# Create ECR repository for backend image
aws ecr create-repository --repository-name global-rails-backend --region af-south-1

# Build and push Docker image
docker build -t global-rails-backend ./backend
docker tag global-rails-backend:latest <account-id>.dkr.ecr.af-south-1.amazonaws.com/global-rails-backend:latest
docker push <account-id>.dkr.ecr.af-south-1.amazonaws.com/global-rails-backend:latest

# Create a secret in Secrets Manager
aws secretsmanager create-secret \
  --name "global-rails/mpesa-consumer-key" \
  --secret-string "YOUR_KEY_HERE" \
  --region af-south-1
```

---

