# Deploying OutSource to AWS (ECS + RDS) — Hackathon Guide

A streamlined guide for deploying the OutSource backend to **AWS ECS (Fargate)** with **MySQL on RDS**, designed for **demo/hackathon AWS accounts** with limited IAM permissions.

> **Your local `docker compose up` workflow is unchanged.** All of these changes are additive.

### What makes this different from a production deployment

| Shortcut taken | Why |
|---|---|
| No custom IAM roles — uses pre-existing account roles | Demo accounts often block `iam:CreateRole` / `iam:PassRole` |
| No Secrets Manager — env vars set directly in task definition | Avoids needing Secrets Manager read permissions on the execution role |
| ECS tasks in **public subnets** with public IPs | Eliminates the NAT gateway ($32/mo) and simplifies networking |
| No ALB — direct public IP on the Fargate task | Eliminates the load balancer ($16/mo) and extra setup |
| RDS set to **publicly accessible** | Lets you run schema SQL from your laptop without a bastion host |

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Configure the AWS CLI](#2-configure-the-aws-cli)
3. [Find Your Existing IAM Role](#3-find-your-existing-iam-role)
4. [Set Up Networking (VPC & Security Groups)](#4-set-up-networking-vpc--security-groups)
5. [Create the RDS MySQL Database](#5-create-the-rds-mysql-database)
6. [Initialize the RDS Schema](#6-initialize-the-rds-schema)
7. [Create an ECR Repository & Push Your Docker Image](#7-create-an-ecr-repository--push-your-docker-image)
8. [Create a CloudWatch Log Group](#8-create-a-cloudwatch-log-group)
9. [Register the ECS Task Definition](#9-register-the-ecs-task-definition)
10. [Create an ECS Cluster & Service](#10-create-an-ecs-cluster--service)
11. [Verify the Deployment](#11-verify-the-deployment)
12. [Updating Your App (Redeployments)](#12-updating-your-app-redeployments)
13. [Connecting Your Flutter Frontend](#13-connecting-your-flutter-frontend)

---

## 1. Prerequisites

You should already have:
- **AWS Console access** (URL, username, and password provided by your hackathon organizers)
- **Docker Desktop** installed and running on your Mac
- A terminal (the macOS built-in Terminal or VS Code terminal)

### Pick a Region

All resources must be in the **same AWS region**. Use whatever region your hackathon account defaults to (check the top-right of the AWS Console). Common choices: `us-east-1`, `us-west-2`.

Wherever you see `REGION` below, use your region. Wherever you see `ACCOUNT_ID`, use your 12-digit account ID (visible in the top-right corner of the Console, click your username).

---

## 2. Configure the AWS CLI

### Install the CLI

```bash
brew install awscli
```

### Get Credentials

Your hackathon/demo account likely provides credentials in one of these ways:

**Option A: Access keys provided directly**
Your organizers gave you an Access Key ID and Secret Access Key. Run:
```bash
aws configure
```
```
AWS Access Key ID [None]: <your access key>
AWS Secret Access Key [None]: <your secret key>
Default region name [None]: us-east-1
Default output format [None]: json
```

**Option B: AWS Academy / Learner Lab (Vocareum)**
1. In Vocareum, click **"AWS Details"** → **"Show"** next to AWS CLI
2. Copy the entire block (it includes `aws_access_key_id`, `aws_secret_access_key`, and `aws_session_token`)
3. Paste it into `~/.aws/credentials`:
   ```bash
   nano ~/.aws/credentials
   ```
   Replace all existing content with the copied block. Save with `Ctrl+O`, `Enter`, `Ctrl+X`.
4. Also set your default region:
   ```bash
   aws configure set region us-east-1
   ```

> **Note:** Learner Lab session tokens expire every ~4 hours. You'll need to repeat the credential copy when they expire.

**Option C: SSO / Identity Center**
If your account uses SSO, your organizers will give you an SSO start URL:
```bash
aws configure sso
# Follow the prompts with the URL/region they gave you
```

### Verify

```bash
aws sts get-caller-identity
```
You should see your account number and role. **Note the Account ID** — you'll need it throughout.

---

## 3. Find Your Existing IAM Role

Demo accounts typically have pre-created roles you must use (since you can't create new ones). You need to find a role that ECS can use to pull images from ECR and write logs.

### Check What's Available

```bash
aws iam list-roles --query 'Roles[*].RoleName' --output table
```

Look for any of these common names:
- `ecsTaskExecutionRole` (ideal — purpose-built for ECS)
- `LabRole` (common in AWS Academy accounts — has broad permissions)
- `AWSServiceRoleForECS` (service-linked, but won't work for task execution)
- Anything with `ecs`, `execution`, or `task` in the name

**Get the full ARN of the role you'll use:**
```bash
aws iam get-role --role-name LabRole --query 'Role.Arn' --output text
```

Example output: `arn:aws:iam::123456789012:role/LabRole`

**Write this down — you'll paste it into the task definition.**

> **If you don't see any suitable role** and can't create one, check with your hackathon organizers. Most demo accounts have at least `LabRole` or `ecsTaskExecutionRole` pre-created.

> **AWS Academy / Learner Lab users:** Your role is almost certainly `LabRole`. Its ARN is:
> `arn:aws:iam::<ACCOUNT_ID>:role/LabRole`

---

## 4. Set Up Networking (VPC & Security Groups)

### Use the Default VPC

Every AWS account comes with a **default VPC** and public subnets — no need to create a new one. This is the fastest path.

**Find your default VPC ID:**
1. Go to **AWS Console** → search **VPC** → open it
2. In the left sidebar, click **Your VPCs**
3. You'll see a VPC marked **"Yes"** in the "Default VPC" column
4. Note its **VPC ID** (e.g., `vpc-0abc123...`)

**Find your subnet IDs:**
1. In the VPC dashboard, click **Subnets** in the left sidebar
2. Filter by your default VPC
3. Note **at least 2 subnet IDs** in different Availability Zones (e.g., `subnet-aaa...` in `us-east-1a` and `subnet-bbb...` in `us-east-1b`)
   - RDS requires subnets in at least 2 AZs

### Create Security Groups

You need 2 security groups: one for RDS, one for ECS.

#### Security Group 1: RDS

1. Go to **VPC** → **Security Groups** → **Create security group**
2. Settings:
   - Security group name: `outsource-rds-sg`
   - Description: `MySQL access for OutSource`
   - VPC: your **default VPC**
3. **Inbound rules** → **Add rule**:
   - Type: **MySQL/Aurora** (auto-fills port 3306)
   - Source: **My IP** (so you can connect from your laptop to initialize the schema)
4. Click **Create security group**
5. **Note the Security Group ID** (e.g., `sg-0rds...`)

#### Security Group 2: ECS

1. Go to **VPC** → **Security Groups** → **Create security group**
2. Settings:
   - Security group name: `outsource-ecs-sg`
   - Description: `ECS task access for OutSource`
   - VPC: your **default VPC**
3. **Inbound rules** → **Add rule**:
   - Type: **Custom TCP**
   - Port range: `8000`
   - Source: **Anywhere (0.0.0.0/0)** (allows API access from anywhere)
4. Click **Create security group**
5. **Note the Security Group ID** (e.g., `sg-0ecs...`)

#### Allow ECS → RDS

Now update the RDS security group to also allow traffic from ECS:
1. Go back to **Security Groups** → select `outsource-rds-sg`
2. **Inbound rules** tab → **Edit inbound rules** → **Add rule**
   - Type: **MySQL/Aurora** (port 3306)
   - Source: select the **`outsource-ecs-sg`** security group
3. **Save rules**

You should now have 2 inbound rules on `outsource-rds-sg`: one for your IP, one for `outsource-ecs-sg`.

---

## 5. Create the RDS MySQL Database

1. Go to **AWS Console** → search **RDS** → open it
2. Click **Create database**
3. Settings:
   - **Choose a database creation method**: Standard create
   - **Engine**: MySQL
   - **Engine version**: MySQL 8.0.x (whatever latest 8.0 is available)
   - **Templates**: **Free tier** (if available) or **Dev/Test**
   - **DB instance identifier**: `outsource-db`
   - **Master username**: `outsource_admin`
   - **Credentials management**: Self managed
   - **Master password**: pick something and **write it down** (e.g., `HackathonPass123!`)
   - **DB instance class**: `db.t3.micro` (or `db.t4g.micro` if t3 isn't available)
   - **Storage**: 20 GB gp3 (defaults are fine)
   - **Connectivity**:
     - VPC: **Default VPC**
     - **Public access**: **Yes** ← important! This lets you connect from your laptop
     - VPC security group: **Choose existing** → select `outsource-rds-sg` → **remove** the `default` SG if auto-added
     - Availability Zone: **No preference**
   - **Additional configuration** (expand this section):
     - Initial database name: `outsource_db`
     - Uncheck **"Enable automated backups"** (not needed for a hackathon)
     - Uncheck **"Enable encryption"** if it causes permission errors
4. Click **Create database**
5. Wait **5-10 minutes** for status to become **"Available"**

### Find Your RDS Endpoint

1. Go to **RDS** → **Databases** → click `outsource-db`
2. Under **Connectivity & security**, copy the **Endpoint** (e.g., `outsource-db.c9abc123.us-east-1.rds.amazonaws.com`)
3. Port is `3306`

Your `DATABASE_URL` is:
```
mysql+pymysql://outsource_admin:HackathonPass123!@outsource-db.c9abc123.us-east-1.rds.amazonaws.com:3306/outsource_db
```

---

## 6. Initialize the RDS Schema

Since the RDS instance is publicly accessible and your IP is allowed in the security group, you can connect directly from your laptop.

### Install the MySQL Client (if not already installed)

```bash
brew install mysql-client
# Add to PATH if brew tells you to:
echo 'export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Run the Schema & Seed Data

From the `backend/` directory:

```bash
cd /path/to/OutSource/backend

# Run the schema creation script
mysql -h outsource-db.c9abc123.us-east-1.rds.amazonaws.com \
  -u outsource_admin \
  -p'HackathonPass123!' \
  outsource_db < create-schema.sql

# Run the seed data script
mysql -h outsource-db.c9abc123.us-east-1.rds.amazonaws.com \
  -u outsource_admin \
  -p'HackathonPass123!' \
  outsource_db < insert-info.sql
```

> **Note:** No space between `-p` and the password. If your password has special characters like `!`, wrap the whole flag in single quotes: `-p'MyPass!'`

### Verify

```bash
mysql -h outsource-db.c9abc123.us-east-1.rds.amazonaws.com \
  -u outsource_admin \
  -p'HackathonPass123!' \
  outsource_db -e "SHOW TABLES;"
```

You should see your tables listed.

---

## 7. Create an ECR Repository & Push Your Docker Image

ECR (Elastic Container Registry) is AWS's private Docker image registry.

### Create the Repository

1. Go to **AWS Console** → search **ECR** → open **Elastic Container Registry**
2. Click **Get started** or **Create repository**
3. Visibility: **Private**
4. Repository name: `outsource-api`
5. Leave everything else as default → **Create repository**

### Build and Push

Run these from the `backend/` directory. Replace `ACCOUNT_ID` and `REGION` with your values:

```bash
cd /path/to/OutSource/backend

# 1. Authenticate Docker with ECR
aws ecr get-login-password --region REGION | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com

# 2. Build the image (--platform is critical for Apple Silicon Macs)
docker build --platform linux/amd64 -t outsource-api .

# 3. Tag for ECR
docker tag outsource-api:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/outsource-api:latest

# 4. Push
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/outsource-api:latest
```

> **Apple Silicon (M1/M2/M3/M4) Macs**: The `--platform linux/amd64` flag is critical. Fargate runs x86_64 and will crash with an ARM image.

Verify in the Console: **ECR** → `outsource-api` → you should see a `latest` image.

---

## 8. Create a CloudWatch Log Group

This is where your container's stdout/stderr goes (print statements, errors, uvicorn logs).

1. Go to **AWS Console** → search **CloudWatch** → open it
2. In the left sidebar: **Logs** → **Log groups** → **Create log group**
3. Log group name: `/ecs/outsource-api`
4. Retention: **1 week** (or whatever you like)
5. Click **Create**

> **If this fails** due to permissions, don't worry — the task definition includes `"awslogs-create-group": "true"` which will auto-create it when the task first runs (if the execution role allows it).

---

## 9. Register the ECS Task Definition

The task definition is a blueprint telling ECS how to run your container.

### Fill In the Template

Open `backend/ecs-task-definition.json` and replace the placeholder values:

| Placeholder | Replace with | Example |
|---|---|---|
| `EXECUTION_ROLE_ARN` | The role ARN from step 3 | `arn:aws:iam::123456789012:role/LabRole` |
| `ACCOUNT_ID` | Your 12-digit account ID | `123456789012` |
| `REGION` | Your AWS region | `us-east-1` |
| `YOUR_PASSWORD` | Your RDS master password | `HackathonPass123!` |
| `YOUR_RDS_ENDPOINT` | Your RDS endpoint from step 5 | `outsource-db.c9abc123.us-east-1.rds.amazonaws.com` |
| `CHANGE_ME` (JWT_SECRET_KEY) | Any random string | Generate with: `openssl rand -hex 32` |
| `CHANGE_ME` (GEMINI_API_KEY) | Your Google Gemini API key | From https://aistudio.google.com |

### Register It

**Option A: Console (recommended)**
1. Go to **ECS** → **Task definitions** (left sidebar)
2. Click **Create new task definition** → choose **Create new task definition with JSON**
3. **Delete** everything in the editor and **paste** your completed `ecs-task-definition.json`
4. Click **Create**

**Option B: CLI**
```bash
cd /path/to/OutSource/backend
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

---

## 10. Create an ECS Cluster & Service

### Create the Cluster

1. Go to **ECS** → **Clusters** → **Create cluster**
2. Cluster name: `outsource-cluster`
3. Infrastructure: make sure **AWS Fargate (serverless)** is checked
4. Click **Create**
5. Wait a moment for it to show "Active"

### Create the Service

1. Go to **ECS** → **Clusters** → click **`outsource-cluster`**
2. On the **Services** tab → click **Create**
3. **Compute configuration**:
   - Compute options: **Launch type**
   - Launch type: **FARGATE**
4. **Deployment configuration**:
   - Application type: **Service**
   - Family: `outsource-api`
   - Revision: **latest**
   - Service name: `outsource-api-service`
   - Desired tasks: `1`
5. **Networking** (expand this section):
   - VPC: your **default VPC**
   - Subnets: select **at least 2** (the defaults are fine)
   - Security group: click **Use an existing security group** → select **`outsource-ecs-sg`** → **remove** the `default` SG
   - Public IP: **Turned ON** ← critical! This gives your task a public IP so you can reach it
6. **Load balancing**: skip this entirely (choose **None**)
7. Click **Create**

### Wait for it to Start

1. Stay on the **`outsource-cluster`** page → **Tasks** tab
2. After ~1-2 minutes, the task status should change from `PROVISIONING` → `PENDING` → `RUNNING`
3. If it goes to `STOPPED`, click the task → scroll down to see the **Stopped reason** and **Logs** tab for debugging

---

## 11. Verify the Deployment

### Find Your Task's Public IP

1. In **ECS** → **Clusters** → `outsource-cluster` → **Tasks** tab
2. Click on the **running task** (the task ID link)
3. Under the **Configuration** section, find **Public IP** (e.g., `3.95.123.45`)

### Test the API

```bash
# Replace with your task's public IP
curl http://3.95.123.45:8000/

# Expected: {"message":"Welcome to OutSource API"}

curl http://3.95.123.45:8000/health

# Expected: {"status":"healthy"}
```

If both return the expected responses, your deployment is working!

### View Logs

- **Console**: **CloudWatch** → **Log groups** → `/ecs/outsource-api` → click the latest log stream
- **CLI**: `aws logs tail /ecs/outsource-api --follow`

### Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Task stays `PROVISIONING` forever | Subnets don't have internet access | Make sure you're using default VPC public subnets and Public IP is turned on |
| Task starts then immediately `STOPS` | App crash — check logs | CloudWatch → `/ecs/outsource-api` → check error messages |
| `CannotPullContainerError` | ECR auth issue or wrong image URI | Verify the image URI in the task def matches your ECR repo exactly |
| `curl` times out | Security group not open on port 8000 | Check `outsource-ecs-sg` has inbound rule for TCP 8000 from 0.0.0.0/0 |
| `Can't connect to MySQL server` | SG or RDS endpoint wrong | Check `outsource-rds-sg` allows port 3306 from `outsource-ecs-sg`; verify the DATABASE_URL endpoint |
| `AccessDeniedException` on task start | Execution role doesn't have ECR pull permission | Try a different pre-existing role (e.g., `LabRole`); check with organizers |
| Task starts but `/health` returns error | Database not initialized | Re-run the schema scripts from step 6 |

---

## 12. Updating Your App (Redeployments)

After making code changes:

```bash
cd /path/to/OutSource/backend

# 1. Rebuild
docker build --platform linux/amd64 -t outsource-api .

# 2. Tag and push
docker tag outsource-api:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/outsource-api:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/outsource-api:latest

# 3. Force ECS to pull the new image
aws ecs update-service \
  --cluster outsource-cluster \
  --service outsource-api-service \
  --force-new-deployment
```

Then wait 1-2 minutes for the new task to start. The old task stops after the new one is healthy.

> **Important:** The public IP changes on every new deployment (since there's no load balancer). Check the new task's public IP in the ECS console after each redeploy.

---

## 13. Connecting Your Flutter Frontend

Since the task's public IP changes on every deployment, the easiest approach for a hackathon:

1. After deploying (or redeploying), note the new public IP from the ECS task details
2. Update your Flutter app's API base URL to `http://<PUBLIC_IP>:8000`
3. Rebuild/hot-reload the Flutter app

If you want a stable URL without an ALB, you could:
- Use a free service like [nip.io](https://nip.io) for DNS (e.g., `3-95-123-45.nip.io` → resolves to `3.95.123.45`)
- This doesn't give you a permanent URL, but it does give you a domain-style address

---

## Architecture Summary

```
Internet
   │
   ▼ port 8000
┌──────────────────────── Default VPC / Public Subnets ───────────┐
│                                                                 │
│  ECS Fargate Task (public IP)                                   │
│  ┌──────────────────────────┐                                   │
│  │ outsource-api container  │                                   │
│  │ port 8000                │                                   │
│  └───────────┬──────────────┘                                   │
│              │ port 3306                                        │
│              ▼                                                  │
│  RDS MySQL (outsource-db)                                       │
│  publicly accessible (for schema init from laptop)              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Reference: All the IDs You Collected

Keep a scratch note with these values during setup:

```
Account ID:        ___________________________
Region:            ___________________________
Execution Role ARN:___________________________
VPC ID:            ___________________________
Subnet 1 ID:       ___________________________
Subnet 2 ID:       ___________________________
RDS SG ID:         ___________________________
ECS SG ID:         ___________________________
RDS Endpoint:      ___________________________
RDS Password:      ___________________________
ECR Image URI:     ___________________________
Task Public IP:    ___________________________
```
