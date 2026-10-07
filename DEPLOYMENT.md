# Deployment Guide: Data Cleaning & EDA Studio

This guide details all available methods to deploy the **Data Cleaning & Exploratory Data Analysis (EDA)** project into production or share it online with a live public URL.

---

## Quick Reference Summary

| Deployment Platform | Cost | Setup Time | Best For | Prerequisites |
|---|---|---|---|---|
| **Streamlit Community Cloud** *(Recommended)* | **Free** | ~2 minutes | Portfolios, Demos, Recruiter Sharing | GitHub Account |
| **Hugging Face Spaces** | **Free** | ~3 minutes | Machine Learning / Data Science Portfolio | Hugging Face Account |
| **Render** | **Free tier** | ~5 minutes | Cloud Web Service / Production | Render Account |
| **Docker Container** | Free / VPS | ~2 minutes | Local, AWS EC2, DigitalOcean, GCP | Docker installed |

---

## Method 1: Streamlit Community Cloud (Recommended & 100% Free)

Streamlit Community Cloud is the fastest, simplest, and most reliable hosting platform for Streamlit applications. It pulls directly from your GitHub repository and automatically redeploys whenever you push updates.

### Step 1: Push Changes to GitHub
Make sure your latest code and configuration are committed and pushed to GitHub:
```bash
git add .
git commit -m "feat: add streamlit web application and cloud deployment configs"
git push origin main
```

### Step 2: Sign In to Streamlit Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io/).
2. Sign in with your **GitHub** account (`balaji-ai2006`).

### Step 3: Deploy the App
1. Click the **"New app"** (or **"Create app"**) button.
2. Fill in the repository details:
   - **Repository:** `balaji-ai2006/data-cleaning-eda-python`
   - **Branch:** `main`
   - **Main file path:** `app.py`
3. Under **Advanced settings** (optional), ensure Python 3.11 or 3.12 is selected.
4. Click **"Deploy!"**.

> [!NOTE]
> Within 1-2 minutes, Streamlit will install `requirements.txt` and launch your app. You will receive a permanent public URL (e.g., `https://data-cleaning-eda-balaji.streamlit.app`).

---

## Method 2: Hugging Face Spaces (Free)

Hugging Face Spaces provides a dedicated cloud environment with free compute for data science applications.

### Steps:
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. Set Space details:
   - **Space Name:** `data-cleaning-eda-studio`
   - **License:** `mit`
   - **Space SDK:** Select **Streamlit**
   - **Space hardware:** `CPU Basic` (Free)
3. Connect your GitHub repository (`balaji-ai2006/data-cleaning-eda-python`) or clone the Hugging Face git remote and push your files.
4. Hugging Face will automatically detect `requirements.txt` and launch `app.py`.

---

## Method 3: Render (Free Web Service)

Render provides free cloud hosting with automated SSL and custom domain support.

### Steps:
1. Sign up / log in to [render.com](https://render.com/).
2. Click **"New +"** $\rightarrow$ **"Web Service"**.
3. Connect your GitHub repository: `balaji-ai2006/data-cleaning-eda-python`.
4. Configure the service:
   - **Name:** `data-cleaning-eda-studio`
   - **Region:** Any (e.g., Oregon / Frankfurt / Singapore)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Instance Type:** `Free`
5. Click **"Create Web Service"**.

*(Alternatively, Render will automatically recognize the included `render.yaml` blueprint if you choose "Blueprint" deployment).*

---

## Method 4: Docker Container Deployment

A production-ready `Dockerfile` and `docker-compose.yml` are already configured in the repository.

### Option A: Using Docker CLI
```bash
# 1. Build the Docker image
docker build -t data-cleaning-eda-app .

# 2. Run the container
docker run -d -p 8501:8501 --name eda-app data-cleaning-eda-app

# 3. Access in browser
http://localhost:8501
```

### Option B: Using Docker Compose
```bash
# Build and start in one command
docker compose up -d

# View logs
docker compose logs -f

# Stop container
docker compose down
```

---

## Method 5: Running Locally

To run the application locally on your machine:

```powershell
# 1. Activate your virtual environment (if using one)
.\.venv\Scripts\Activate.ps1

# 2. Ensure dependencies are installed
pip install -r requirements.txt

# 3. Launch the Streamlit dashboard
streamlit run app.py
```
The app will open automatically in your browser at `http://localhost:8501`.

---

## Verification Checklist

Before deploying, ensure:
- [x] `requirements.txt` contains `streamlit>=1.30.0` and `plotly>=5.18.0` without any formatting errors.
- [x] `app.py` is located in the root directory.
- [x] `.streamlit/config.toml` is present with server and theme settings.
- [x] `sample_data.csv` is present for default sample dataset loading.
- [x] `Dockerfile` and `docker-compose.yml` are ready for container builds.
