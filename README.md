# MyTalker-Demo

## 🛠️ Environment Preparation

This system requires two separate Conda environments to run properly. Please create them using the provided `.yml` configuration files:

### 1. Database Server Environment
```bash
conda env create -f db_server.yml
```

### 2. Main Application Environment
```bash
conda env create -f myTalker_v1.yml
```

---

## 📥 Model Download

Before running the project, you need to download the required pre-trained models. Taking **EGSTalker** as an example, you can choose either of the following methods to download the model files:

* **Open Source Community:** [ICIG/EGSTalker](https://github.com/ICIG/EGSTalker) 
* **Baidu Netdisk:** [百度网盘](https://pan.baidu.com/s/1osTDVG2hCA68Bx5cLVPKfg?pwd=2fpu) *(Extraction Code: `[2fpu]`)*

> **Note:** After downloading, please extract the files and note the absolute path to the model directory.

---

## ⚙️ Configuration

Once the models are successfully downloaded and extracted, you need to configure the project to locate them:

1. Open the following file in your code editor: `Mytalker-Demo/backend/main01.py`
2. Find the model path configuration section inside the script.
3. Modify the paths to point to the absolute folder path where you saved the downloaded models.

---

## 🚀 Usage

Here is the step-by-step guide to run the MyTalker-Demo system on a Linux server and access it locally.

### 1. Terminal Preparation

Open three separate terminal windows connected to your Linux server.
* **Window 1:** Activate the `db_server` environment.
* **Window 2:** Activate the `myTalker_v1` environment.
* **Window 3:** Activate the `myTalker_v1` environment.

### 2. Environment Setup & Dependency Installation

In **Window 2** (with `myTalker_v1` activated), execute the following commands to install Node.js and the required Python backend libraries:

**Install NVM (Node Version Manager) & Node.js:**
```bash
# Download and install NVM
curl -o- [https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh](https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh) | bash

# Refresh environment variables
source ~/.bashrc

# Install the latest LTS version of Node.js
nvm install --lts
```

**Install Frontend Dependencies:**
```bash
cd Mytalker-Demo/frontend
npm install
npm install axios
```

**Install Backend Dependencies:**
```bash
pip install fastapi "uvicorn[standard]" python-multipart
```

### 3. Start the Database Server

In **Window 1** (with `db_server` activated), start the MySQL database service. Replace `[your database path]` with the actual path to your database data directory.
```bash
mysqld --datadir=[your database path] --port=3306 &
```

### 4. Start the Frontend Application

In **Window 2**, navigate to the frontend directory and start the development server.
```bash
cd Mytalker-Demo/frontend
npm run dev
```

### 5. Start the Backend API

In **Window 3**, navigate to the backend directory and launch the Python backend application.
```bash
cd Mytalker-Demo/backend
python main01.py
```

### 6. Set Up SSH Port Forwarding

To access the server's web interface securely from your local machine, open a terminal (CMD or PowerShell) on your **Local Computer** and create an SSH tunnel.
```bash
ssh -L 5173:127.0.0.1:5173 -L 8000:127.0.0.1:8000 [username]@[server address]
```

### 7. Access the Application

Once the SSH tunnel is active, open your local web browser and navigate to the address provided by the frontend console (usually `http://localhost:5173` or similar). You can now explore and use the MyTalker system!
