# AI-Powered Customer Churn Prediction and Retention System

## Project Overview

The **AI-Powered Customer Churn Prediction and Retention System** is a machine learning project designed to predict customer churn and help businesses identify customers who may be at risk of leaving.

The project combines machine learning, data preprocessing, a Flask web application, PostgreSQL database integration, and Power BI reporting to demonstrate an end-to-end data science workflow.

## Key Features

* Customer churn prediction using a trained Random Forest model.
* Data cleaning, preprocessing, and feature engineering.
* Customer registration and login.
* Customer dashboard with personalized information.
* Prediction history tracking.
* Admin dashboard for customer and prediction analytics.
* Churn risk classification and retention recommendations.
* Power BI dashboards for data visualization.

## Technology Stack

* **Programming:** Python, SQL, HTML, CSS
* **Machine Learning:** Pandas, NumPy, Scikit-learn
* **Web Framework:** Flask
* **Database:** PostgreSQL
* **Visualization:** Power BI, Matplotlib, Seaborn
* **Development Tools:** Jupyter Notebook, Visual Studio Code, Git, GitHub

## Project Structure

```text
AI-Powered-Customer-Churn-Prediction-System/
│
├── App/
│   ├── Templates/
│   ├── models/
│   └── app.py
│
├── Dashboard/
│   └── churn.pbix
│
├── NoteBooks/
│   ├── 01_data_generation.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_EDA.ipynb
│   ├── 04_PreProcessing.ipynb
│   ├── Data/
│   ├── models/
│   └── churn.pbix
│
├── .gitignore
└── README.md
```

## Machine Learning Workflow

1. Generate customer data for analysis.
2. Clean missing values and prepare the dataset.
3. Perform exploratory data analysis (EDA).
4. Engineer useful customer features.
5. Preprocess numerical and categorical variables.
6. Train and evaluate machine learning models.
7. Use the trained model to predict customer churn.
8. Display customer risk information through the Flask application and Power BI dashboards.

## Getting Started

### Prerequisites

Install Python and PostgreSQL. Ensure Git is available on your system.

### 1. Clone the repository

```bash
git clone https://github.com/AshishJagadhane/AI-Powered-Customer-Churn-Prediction-System.git
```

### 2. Open the project folder

```bash
cd AI-Powered-Customer-Churn-Prediction-System
```

### 3. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install the required packages

Install the Python libraries used by the application and notebooks, including Flask, pandas, NumPy, scikit-learn, and the PostgreSQL database driver used in `App/app.py`.

### 5. Configure the database

Create the PostgreSQL database and configure the database connection using your own local credentials. Configure any required environment variables before running the application. Never commit passwords, secret keys, or `.env` files to GitHub.

### 6. Run the Flask application

From the project root, run:

```powershell
python App/app.py
```

Open the local address shown in the terminal in your browser.

**Note:** Database configuration and Python dependencies must be set up before the application can run successfully. Use the existing application code to confirm the exact database settings and required packages.

## Business Value

Customer churn prediction can help businesses:

* Identify customers who may be likely to leave.
* Prioritize high-risk customers for follow-up.
* Support data-driven customer retention strategies.
* Monitor customer trends through dashboards and reports.

## Future Improvements

* Deploy the application to a cloud platform.
* Add automated model retraining and monitoring.
* Improve model explainability with feature importance and SHAP.
* Add more advanced customer retention analytics.

## Author

**Ashish Jagadhane**

Master's Student in Computer Science | Data Analytics | Machine Learning

GitHub: [AshishJagadhane](https://github.com/AshishJagadhane)
