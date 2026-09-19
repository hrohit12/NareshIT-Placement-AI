# How to Run NareshIT Placement AI

Welcome to the NareshIT Placement AI! This project consists of a Python Flask backend (`app.py`) that serves a web application and uses a custom AI job searching agent (`ai_job_agent.py`) to scrape and process live job listings.

Follow these step-by-step instructions to get the project running on your local machine.

## Prerequisites
- **Python 3.10+** installed on your system.
- A **Google Gemini API Key** (You can get one for free from Google AI Studio).

---

## Step-by-Step Setup

### 1. Open your Terminal
Navigate to the root directory of the project in your terminal:
```bash
cd /path/to/job_agent
```

### 2. Set Up a Python Virtual Environment
It is highly recommended to use a virtual environment so the project's dependencies don't interfere with your system Python.
```bash
# Create the virtual environment
python3 -m venv venv

# Activate the virtual environment (macOS/Linux)
source venv/bin/activate

# (If you are on Windows, use this instead:)
# venv\Scripts\activate
```

### 3. Install Dependencies
Install all required Python libraries (Flask, requests, beautifulsoup4, google-genai, etc.):
```bash
pip install -r requirements.txt
```

### 4. Configure Your API Key
The AI Job Agent requires a Gemini API key to parse the job listings and generate resumes.
1. Create a file named `.env` in the same directory as `app.py`.
2. Open the `.env` file and add your API key like this:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
*(Note: A `.env.example` file is provided for reference.)*

---

## Running the Application

### 1. Start the Backend Server
Make sure your virtual environment is still activated, then run the Flask web server:
```bash
python app.py
```
You should see output indicating that the server is running on `http://127.0.0.1:5000/`.

### 2. Access the Web App
Open your favorite web browser (Chrome, Safari, Firefox, etc.) and navigate to:
[http://127.0.0.1:5000/](http://127.0.0.1:5000/)

---

## How It Works Under the Hood

- **The UI (`index.html`, `script.js`, `style.css`)**: This is the frontend you see in your browser. When you fill out a search form and click "Search", the frontend sends an API request to your Python server.
- **The Server (`app.py`)**: This script acts as the "middleman". It receives the request from the UI, geocodes the location, and then asks `ai_job_agent.py` to go fetch the jobs.
- **The AI Agent (`ai_job_agent.py`)**: This is the engine of the operation. It automatically scrapes DuckDuckGo's raw HTML to find job postings on LinkedIn, Indeed, and Foundit. It then sends that messy raw text to the **Gemini AI**, which intelligently structures the jobs into a clean, standard format. 
- **The Result**: `ai_job_agent.py` hands the clean jobs back to `app.py`, which hands them back to your browser to be plotted beautifully on the map!

## Troubleshooting

- **"Failed to fetch jobs" error in UI**: This usually means the Flask server (`app.py`) has stopped running or crashed. Check your terminal for error logs and make sure the server is still running.
- **"ModuleNotFoundError"**: Make sure you activated your virtual environment (`source venv/bin/activate`) before running `python app.py`.
- **0 Jobs Found constantly**: Ensure your `.env` file contains a valid `GEMINI_API_KEY`. If the key is invalid or quota is exceeded, the AI agent won't be able to extract the jobs.

---

## Deployment (Render)

This application is configured for easy deployment on [Render](https://render.com). The project uses **Flask-SQLAlchemy** so it can gracefully switch from local SQLite to production PostgreSQL without code changes.

1. Push this repository to GitHub.
2. Sign in to Render, click **New > Blueprint**.
3. Connect your GitHub repository.
4. Render will use the included `render.yaml` file to provision the web service (using `gunicorn`), provision a PostgreSQL database, and wire them together.
5. In the Render dashboard, navigate to your new web service's **Environment** tab and add your `GEMINI_API_KEY`.
