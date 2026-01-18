---
title: JNTU Results Dashboard
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: 1.41.1
app_file: app.py
pinned: false
---

# JNTU Dashboard

This is a full-stack data pipeline designed to scrape student results from the JNTU web portal, extract personal data from administrative PDFs, store structured data in SQLite, and visualize academic performance via an interactive dashboard.

## Overview

This system automates the processing of JNTU (R20 Regulation) results. It handles the complexity of "Regular", "Honors", and "Minors" degree classifications, tracks backlogs across supplementary exams, and generates deep insights into student and batch performance.

## Key Features

* **Automated Web Scraping**: Iterates through semester URLs to fetch Regular and Supplementary results using **Playwright**.

* **Intelligent SGPA/CGPA Calculation**: Automatically separates Honors/Minors credits from Regular credits to prevent GPA inflation.

* **PDF Data Extraction**: Parses administrative PDFs to extract student photos, phone numbers, and addresses using **pdfplumber** and **PyMuPDF**.

* **Interactive Dashboard**: A **Streamlit** application offering views for Cohort Analysis, Subject Difficulty (Failure Rates), Student History, and Topper Lists.

* **Backlog Tracking**: Visualizes active vs. cleared backlogs and identifies detained students.

## Tech Stack

* **Language**: Python 3.8+
* **Web Scraping**: Playwright, BeautifulSoup4
* **Data Extraction**: pdfplumber, PyMuPDF (fitz)
* **Database**: SQLite3
* **Visualization**: Streamlit, Plotly Express
* **Data Manipulation**: Pandas, NumPy

## Project Structure

```text
.
├── app.py                 # Streamlit dashboard application
├── extract.py             # PDF extraction script (Personal data & Photos)
├── scrape.py              # Main scraping logic & Database management
├── Results.db             # SQLite database storing all student data
├── JNTU IT.pdf            # Input PDF for personal data extraction
├── Extraction_Output/     # Generated output directory
│   ├── Results.csv        # Extracted personal details
│   └── Student_Photos/    # Extracted student images
└── requirements.txt       # Python dependencies

```

## Database Schema

The system uses a normalized SQLite database (`Results.db`) with the following tables:

* **`students`**: Personal details (Name, Hall Ticket, Phone, Address, Photo).
* **`semester_results`**: SGPA, Credits, and Status per semester.
* **`marks`**: Subject-wise grades and credits (linked to `semester_results`).
* **`exam_history`**: A comprehensive log of every exam attempt (Regular & Supply).
* **`overall_cgpa`**: Calculated Cumulative GPA, Degree Class, and Honors/Minors status.

## Installation

1. **Clone the repository**:
```bash
git clone "https://github.com/msrsaditya/JNTU-Results"
cd JNTU-Results

```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt

```

3. **Install Playwright browsers**:
```bash
playwright install chromium

```

## Usage Pipeline

Execute the scripts in the following order to build the dataset and launch the dashboard.

### 1. Data Extraction (Optional)

If you have the student list PDF (e.g., `JNTU IT.pdf`), run this first to extract photos and personal info (setup Python virtual environment first using uv).

```bash
python extract.py

```

* *Input:* `JNTU IT.pdf`
* *Output:* `Extraction_Output/Results.csv` and `Extraction_Output/Student_Photos/`.

### 2. Result Scraping & Processing

Runs the main scraper. This initializes the database, scrapes results from JNTU, fills lateral entry gaps, recalculates CGPA, and merges the extraction data from Step 1.

```bash
python scrape.py

```

* *Note:* Ensure the URL constants (`REGULAR_URLS`, `SUPPLY_URLS`) inside `scrape.py` are up to date.

### 3. Launch Dashboard

Start the visualization interface.

```bash
streamlit run app.py

```

* Access the dashboard in your browser at `http://localhost:8501`.

## Configuration

* **Result Links**: Update the `REGULAR_URLS`, `SUPPLY_URLS`, `MINORS_URLS`, and `HONORS_URLS` dictionaries in `scrape.py` with the specific result URLs for the current batch.

* **PDF Source**: Update `INPUT_PDF_FILE` in `extract.py` if your source file has a different name.

* **Roll Number Ranges**: Modify the `regular_rolls` and `lateral_rolls` ranges in the `__main__` block of `scrape.py` to match the target batch.

## Disclaimer

This tool is for educational and analytical purposes only. Ensure you have the necessary permissions to scrape and store student data. The "Failure Rate" and "Difficulty" metrics in the dashboard are statistical derivations and do not reflect official university difficulty ratings.

### Lines of Code
![Lines of Code](https://github.com/msrsaditya/JNTU-Results/blob/main/Lines%20of%20Code.png)
