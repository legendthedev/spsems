# SPSEMS � 24/7 Live Hosting Guide (100% Free)

This guide walks you through hosting the **KWASU SPSEMS** full-stack system online so it can be accessed on any device 24/7 for free.

---

## Architecture at a Glance

* **Frontend**: Hosted on **Vercel** (Global CDN + automatic HTTPS).
* **Backend & ML Microservice**: Hosted on **Render** (Free Python Web Services).
* **Database**: Hosted on **Supabase** (Free 24/7 Cloud PostgreSQL).

---

## Step 1: Push Your Project to GitHub

1. Open your terminal in VS Code (in the `spsems` folder).
2. Run these commands:

```bash
git init
git add .
git commit -m "Initial commit for 24/7 live hosting"
git branch -M main
```

3. Go to [GitHub](https://github.com/new) and create a new repository named `spsems` (keep it Public or Private).
4. Connect and push your code:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/spsems.git
git push -u origin main
```

---

## Step 2: Set Up the Free Database on Supabase (2 mins)

1. Sign up at [supabase.com](https://supabase.com) and click **"New Project"**.
2. Give it a name (e.g. `spsems`), set a **Database Password** (remember this!), and choose a region.
3. Once the project loads, click **SQL Editor** in the left sidebar.
4. Open the file `database/schema_postgres.sql` in your VS Code, copy all the code, paste it into the Supabase SQL Editor, and click **"Run"**.
   * *This creates all tables and demo accounts automatically.*
5. Go to **Project Settings** (gear icon) ? **Database** ? scroll down to **Connection String** ? select **URI**.
6. Copy the connection string. It looks like:
   ```
   postgresql://postgres.[REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   *Replace `[YOUR-PASSWORD]` with the password you set in step 2. Save this for Step 3.*

---

## Step 3: Deploy Backend & ML Service on Render (3 mins)

1. Sign up or log in at [render.com](https://render.com).
2. Click **"New +"** (top right) ? select **"Blueprint"**.
3. Connect your GitHub repository (`spsems`).
4. Render will automatically read the `render.yaml` file in your repository and set up two services:
   * `spsems-ml-service`
   * `spsems-backend`
5. On the setup screen, find the environment variable for `spsems-backend`:
   * **Key**: `DATABASE_URL`
   * **Value**: Paste your Supabase URI from Step 2.
6. Click **"Apply"**.
7. Render will build and launch both services. When finished, copy your Backend public URL:
   * Example: `https://spsems-backend.onrender.com`

---

## Step 4: Deploy Frontend on Vercel (2 mins)

1. Sign up or log in at [vercel.com](https://vercel.com).
2. Click **"Add New..."** ? **"Project"**.
3. Import your `spsems` GitHub repository.
4. On the configuration page:
   * **Root Directory**: Click "Edit" and choose `frontend`.
   * **Framework Preset**: Create React App (automatically detected).
5. Open **"Environment Variables"** and add:
   * **Key**: `REACT_APP_API_URL`
   * **Value**: `https://<YOUR-RENDER-BACKEND-URL>/api`
     *(Example: `https://spsems-backend.onrender.com/api` � make sure to include `/api` at the end!)*
6. Click **"Deploy"**.

---

## ?? You're Live!

Vercel will give you a live URL (e.g. `https://spsems.vercel.app`).
You can now open this link on **any phone, tablet, or computer anywhere in the world**!

### Demo Login Accounts (Password for all: `password123`)

| Role | Username | Email |
| :--- | :--- | :--- |
| **Admin / HOD** | `admin` | `hod@kwasu.edu.ng` |
| **Supervisor** | `supervisor1` | `shakirat@kwasu.edu.ng` |
| **Student** | `student1` | `student1@kwasu.edu.ng` |

#25@detheDev32
#postgresql://postgres:25@detheDev32@db.pblqhptrgrpfcxuwjknb.supabase.co:5432/postgres