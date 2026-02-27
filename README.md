# Equity Injection Concept

A Streamlit web application for tracking and sourcing equity injection funds during a commercial loan closing.

## What It Does

The app helps loan officers and closing teams verify that equity injection funds are properly documented and sourced. It provides a ledger of all expenditures, document sourcing for each line item, and a PDF export of the complete closing package.

## Features

- Ledger to track funds used, vendors, amounts, and bank accounts
- Document sourcing — attach invoices and bank statements to each ledger entry
- Mark items as sourced or unsourced with running totals
- Request missing documents and draft a borrower email
- Export a closing package as a single PDF
- Demo data and sample documents included for testing

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate demo documents (optional):

```bash
python generate_examples.py
```

Run the app:

```bash
streamlit run app.py
```

## Project Structure

```
app.py                  Main application
generate_examples.py    Script to generate demo invoices and statements
demo_data.csv           Sample ledger data
invoices/               Invoice image files
statements/             Bank statement image files organized by account
requirements.txt        Python dependencies
```
