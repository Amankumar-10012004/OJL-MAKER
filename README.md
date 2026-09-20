# OJT Journal Maker

A **Daily Activity Journal PDF Auto-Filler**. Upload your OJT (On-the-Job Training) PDF template, paste your internship work using our structured Markdown format, and the app intelligently generates professional journal content and fills every page of your PDF—automatically.

---

## ✨ Features

- **Offline & Privacy First** – 100% locally processed, no external API calls needed.
- **Markdown-Based Workflow** – Uses a structured Markdown input system for precise control over daily entries.
- **Smart Work Splitting** – Automatically aligns your internship work across all working days, respecting weekends and skip dates.
- **PDF Template Filling** – Overlays generated text onto your existing PDF template seamlessly.
- **Clean UI** – Premium dark-themed single-page app: upload → review → download.

---

## 🗂 File Structure

```
OJL-Maker/
├── main.py             # FastAPI backend (API endpoints + background task)
├── gemini_helper.py    # Text parsing and Markdown splitting logic
├── pdf_filler.py       # PDF overlay filling (ReportLab + PyPDF2)
├── requirements.txt    # Python dependencies
├── static/
│   └── index.html      # Single-page frontend (vanilla HTML5/CSS3/JS)
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- **Python 3.8 or higher** installed on your system.
- **Git** (optional, for cloning the repository).

### 1. Clone the Repository
```bash
git clone https://github.com/MrCode-2005/OJL-Maker.git
cd OJL-Maker
```

### 2. Create and Activate Virtual Environment

#### 🐧 Linux & 🍎 macOS
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
```

#### 🪟 Windows
```bash
# Create venv
python -m venv venv

# Activate venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
uvicorn main:app --reload
```
The app will be available at **http://localhost:8000**.

---

## 🚀 How to Use

### Step 1 – Upload & Configure
1. Open **http://localhost:8000** in your browser.
2. Drag-and-drop (or click to upload) your OJT journal **PDF template**. 
3. Fill in:
   - **Start Date / End Date** – your internship period.
   - **Exclude Dates** – select weekends to exclude or type specific dates.
   - **Trainee Details** – (Department, Designation, Name, etc.).
4. In the **Daily Work Log** section, click "Copy Example Format" and paste your structured markdown entries.
5. Click **Upload & Process**.

### Step 2 – Review Daily Work
- A scrollable list of day cards appears, one per working day.
- Each card shows the date and an editable textarea with your parsed work for that day.
- Edit any entry as needed.
- Click **✨ Generate PDF** when ready.

### Step 3 – Generate & Download
- A progress bar tracks each journal entry being generated and filled into the PDF.
- When complete, click **⬇️ Download PDF** to save your finished journal.

---

## 🛠 Tech Stack

| Layer     | Technology |
|-----------|-----------|
| **Backend**   | FastAPI, Uvicorn |
| **PDF Processing** | ReportLab (drawing) + PyPDF2 (merging/reading) |
| **Frontend**  | Vanilla HTML5 / CSS3 / JavaScript |
