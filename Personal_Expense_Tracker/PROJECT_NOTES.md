# Project Notes — Personal Expense Tracker & Analysis System

## Problem Statement
Manual expense tracking makes it difficult to understand monthly spending, category-wise expenditure and spending patterns. This project provides a simple web-based application to record and analyze daily expenses.

## Objectives
1. Record expenses with date, category, amount and description.
2. Upload supporting bills or receipts.
3. Calculate total, monthly and average expenditure.
4. Identify highest and lowest expenses.
5. Search, filter, sort and delete records.
6. Display monthly and category-wise graphical reports.

## Technology
Python handles the HTTP server, validation, calculations, file handling and chart generation. HTML provides page structure and forms. CSS provides the responsive interface. JSON stores records locally and Matplotlib generates PNG charts for display in the browser.

## Modules
Dashboard; Add Expense and Receipt Upload; Transaction Management; Analysis and Reporting; File Storage.

## Add Expense Algorithm
1. Read the submitted form values.
2. Validate date, amount, description and category.
3. Validate the optional receipt and save it in uploads.
4. Create a unique expense record.
5. Append the record to the JSON file.
6. Reload the transaction list; dashboard figures and charts use the updated data.

## Delete Expense Algorithm
1. Receive the selected expense ID.
2. Find the matching record.
3. Delete its receipt file, if available.
4. Save the remaining records to the JSON file.
5. Reload the page and recalculate all figures and charts.

## Testing
- Valid amount/date: record is saved.
- Empty description, invalid date, zero or negative amount: rejected.
- Unsupported receipt extension or file over 8 MB: rejected.
- Delete a record: it disappears and totals/charts update.
- Restart server: previously saved records remain available.

## Limitation
This is a local single-user academic project. It does not include login, cloud synchronization or multi-user access. Records are stored in a JSON file rather than a database.
