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

* **Open Source Community:** [ICIG/EGSTalker](https://huggingface.co/ICIG/EGSTalker) 
* **Baidu Netdisk:** [百度网盘](https://pan.baidu.com/s/1osTDVG2hCA68Bx5cLVPKfg?pwd=2fpu) *(Extraction Code: `[2fpu]`)*

> **Note:** After downloading, please extract the files and note the absolute path to the model directory.

---

## ⚙️ Configuration

Once the models are successfully downloaded and extracted, you need to configure the project to locate them:

1. Open the following file in your code editor: `Mytalker-Demo/backend/main01.py`
2. Find the model path configuration section inside the script.
3. Modify the paths to point to the absolute folder path where you saved the downloaded models.
