# SpendWise — Personal Expense Tracker & Analysis System

A syllabus-oriented MCA project built with Python's built-in HTTP server, HTML and CSS. No Flask, database server, JavaScript framework or external chart library is required.

## Features
- Add expenses with date, category, amount and description.
- Upload bill/receipt files (JPG, JPEG, PNG or PDF; max 8 MB).
- View transactions, search, filter and sort by date or amount.
- Delete records; dashboard totals and charts recalculate automatically.
- Dashboard cards for total expenditure, this-month expenditure, transaction count and average.
- Analysis includes monthly line chart, category bar chart, donut chart, monthly summary, category summary, highest and lowest expense.
- Data persists locally in `data/expenses.json`; receipt files are saved in `uploads/`.
- Server-side validation for amount, date, category and uploaded file.

## Requirements
Python 3.9 or later. Install Matplotlib with `pip install -r requirements.txt`.

## Run in VS Code
1. Extract the ZIP and open the `Personal_Expense_Tracker` folder in VS Code.
2. Open Terminal → New Terminal.
3. Run `python app.py` (on some systems use `python3 app.py`).
4. Open **http://127.0.0.1:8000** in your browser.
5. Keep the terminal running while using the website. Press Ctrl+C to stop.

## Folder structure
```text
Personal_Expense_Tracker/
├── app.py
├── data/
│   └── expenses.json
├── static/
│   └── style.css
├── uploads/
│   └── .gitkeep
├── README.md
└── PROJECT_NOTES.md
```

## Notes
Charts are generated as PNG images using Matplotlib on each Dashboard and Analysis page request. Adding or deleting an expense changes the values and plotted line/bar segments automatically. The project uses ordinary HTML forms and server-rendered pages, so JavaScript is not required. Back up both `data` and `uploads` to preserve your records and bills.
