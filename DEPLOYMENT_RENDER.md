# Deploying CaFinIQ to Render

This guide provides step-by-step instructions for deploying the **CaFinIQ Bank Statement Intelligence Platform** to [Render](https://render.com/).

---

## Architecture Overview

The entire full-stack application (FastAPI backend + React SPA frontend + OCR & parsing pipeline + Excel generator) is packaged into a **single production Docker container**:
* **Frontend**: Built via multi-stage Node 20 build (`npm run build`), served directly by FastAPI as high-speed static assets.
* **Backend**: Python 3.11 with PyMuPDF, RapidOCR, OpenCV, pdfplumber, and openpyxl.
* **API Endpoints**: All API requests route to `/api/v1` on the same domain with **zero CORS configuration** needed.
* **Health Check**: Available at `/health`.

---

## Method 1: Deploy with Git & Render Blueprint (Recommended - 2 Minutes)

### Step 1: Push Code to GitHub / GitLab
In your terminal:
```bash
git init
git add .
git commit -m "Production release for Render deployment"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

### Step 2: Connect to Render
1. Go to [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** in the top navigation bar.
3. Select **Blueprint**.
4. Connect your GitHub/GitLab repository.
5. Render will automatically detect [`render.yaml`](file:///C:/Users/DELL/Desktop/banksatamentconvertor/render.yaml) and configure:
   * Service Name: `cafiniq-bank-statement-intelligence`
   * Environment: `Docker`
   * Health Check: `/health`
   * Port: `10000`
   * Auto-generated JWT Secret Key
6. Click **Apply**.
7. Render will build and deploy the container automatically!

---

## Method 2: Manual Web Service Deployment (Free Tier Compatible)

If you prefer to deploy manually without a Blueprint:

1. Go to [Render Dashboard](https://dashboard.render.com/) -> Click **New +** -> **Web Service**.
2. Select your repository.
3. Configure the following settings:
   * **Name**: `cafiniq-bank-statement-intelligence` (or your choice)
   * **Region**: `Oregon` (or closest to your users)
   * **Branch**: `main`
   * **Runtime**: **Docker**
   * **Dockerfile Path**: `./Dockerfile`
   * **Instance Type**: **Free** (or Starter for persistent storage)
4. Under **Advanced** -> **Environment Variables**, add:
   * `PORT`: `10000`
   * `PROJECT_NAME`: `CaFinIQ - Bank Statement Intelligence Platform`
   * `SECRET_KEY`: `<Generate a random 32+ character string>`
   * `ACCESS_TOKEN_EXPIRE_MINUTES`: `1440`
   * `MASK_ACCOUNTS_BY_DEFAULT`: `true`
5. Under **Health Check Path**, enter: `/health`.
6. Click **Create Web Service**.

---

## Default Seed Login Credentials

Once deployment completes, open your Render URL (e.g., `https://cafiniq-bank-statement-intelligence.onrender.com`):

* **Email**: `ca@mehtaca.com`
* **Password**: `AuditPassword123!`
* **Firm**: K. R. Mehta & Associates, Chartered Accountants

---

## Free Tier vs. Paid Tier Notes

| Feature | Free Tier | Starter Plan ($7/mo) |
| :--- | :--- | :--- |
| **Compute** | 512 MB RAM, 0.1 CPU | 512 MB+ dedicated CPU |
| **Sleep on Idle** | Spins down after 15 min inactivity | Stays awake 24/7 |
| **Storage** | Ephemeral (resets on restart) | **Persistent Disk (10 GB)** |
| **PostgreSQL** | Free Render PostgreSQL available | Managed PostgreSQL |

*If deploying on the Free tier, make sure to comment out or omit the `disk` section in `render.yaml`, as persistent disks require a Starter plan or above.*
