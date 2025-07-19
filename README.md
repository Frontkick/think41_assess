# 📊 Spreadsheet API

A simple Flask-based spreadsheet backend that supports cell values, formulas, dependency tracking, and recalculation order with cycle detection.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker (optional)

---

## 🔧 Running the App

### 1. Local (Without Docker)

Install dependencies:

```bash
pip install -r requirements.txt
```

run app:
```bash
python app.py
```

###  2. With Docker

```bash
docker build -t app .

docker run app
```



URL:

POST /spreadsheets/{spreadsheet_id}/cells/{cell_id}/value

Example:

POST /spreadsheets/sheet1/cells/A1/value

Request Body:

```
{
  "value": "42"
}
```

URL:

POST /spreadsheets/{spreadsheet_id}/cells/{cell_id}/formula

Example:

POST /spreadsheets/sheet1/cells/A2/formula

Request Body:
```
{
  "formula_string": "=A1+5"
}
```

URL:

GET /spreadsheets/{spreadsheet_id}/cells/{cell_id}

Example:

GET /spreadsheets/sheet1/cells/A1

Response:

```
{
  "cell_id": "A1",
  "value": "42",
  "formula_string": null
}
```

🔗 Get Cell Dependents

URL:

GET /spreadsheets/{spreadsheet_id}/cells/{cell_id}/dependents

Example:

GET /spreadsheets/sheet1/cells/A1/dependents

Response:
```
["A2"]
```