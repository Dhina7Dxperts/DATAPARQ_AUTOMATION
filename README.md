# DataParQ Automation Framework

## Project Overview
This project automates the end-to-end testing of the **DataParQ** platform using Selenium WebDriver, PyTest, and the Page Object Model (POM) design pattern.

The automation covers two independent test flows:
- **Manual Upload Flow (TC01 → TC06):** Tests the complete workflow starting with a manual CSV file upload from the local system.
- **GCP Existing File Flow (TC07 → TC10):** Tests the complete workflow by selecting an existing file from a Google Cloud Platform (GCP) bucket, including the Derived Module pipeline.

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Automation Tool | Selenium WebDriver 4.22 (ChromeDriver) |
| Testing Framework | PyTest 8.0 |
| Design Pattern | Page Object Model (POM) |
| Reporting | python-docx (DOCX evidence reports) |
| Data Handling | CSV, JSON |
| Logging | Python `logging` module (custom logger) |
| Environment Config | python-dotenv (`.env` file) |

---

## Project Structure

```text
dataparq_automation/
│
├── pages/                              
│   ├── login_page.py                   
│   ├── home_page.py                    
│   ├── file_setup_page.py              
│   ├── config_page.py                  
│   ├── ingest_page.py                  
│   ├── data_lakehouse_page.py          
│   ├── data_lakehouse_workflow_page.py 
│   ├── data_governance_page.py         
│   ├── derive_page.py                  
│   ├── monitor_page.py                 
│   └── task_page.py                    
│
├── tests/
│   ├── manual/                         
│   │   ├── test_tc01_file_upload.py
│   │   ├── test_tc02_data_governance.py
│   │   ├── test_tc03_Verify_upload_file_in_Monitor_Module.py
│   │   ├── test_tc04_data_lakehouse_workflow.py
│   │   ├── test_tc05_validate_task_status.py
│   │   └── test_tc06_validate_dq_rejected_records.py
│   │
│   └── gcp/                            
│       ├── test_tc07_gcp_bucket_file_selection.py
│       ├── test_tc08_Verify_upload_file_in_Monitor_Module.py
│       ├── test_tc09_data_lakehouse_workflow.py
│       └── test_tc10_derived_module.py
│
├── utils/
│   ├── config.py                       
│   ├── file_reader.py                  
│   ├── logger.py                       
│   ├── network_capture.py              
│   ├── report_generator.py             
│   └── screenshot_manager.py          
├── test_data/                          
├── reports/                            
│   ├── execution_reports/             
│   ├── documents/                      
│   ├── screenshots/                    
│   └── test_data/                      
│
├── run_info.json                       
├── conftest.py                         
├── pytest.ini                          
├── requirements.txt                    
└── .env                                
```

---

## Test Case Execution Flow

### Manual Upload Flow (TC01 → TC06)

| Test Case | Description |
|---|---|
| **TC01** | Login, manually upload a CSV file from `test_data/`, complete the full ingestion wizard (File Setup → Config → Ingest), and deploy the pipeline. |
| **TC02** | Navigate to the Data Governance module. Upload the governance file and validate it against the ingested data. |
| **TC03** | Open the Monitor module. Create a new batch, search for the domain, open task details, and wait for all tasks to reach `Completed` status (30 min max, 15s polling). |
| **TC04** | Navigate to the Data Lakehouse Workflow page. Create a DQ rule (Business DQ / Rejection), configure the Business Key column dynamically, and deploy the pipeline. |
| **TC05** | Open the Monitor module. Validate that the Data Quality and Data Lake task layers reach `Completed` status. |
| **TC06** | Validate that the rejected record count shown in the UI matches the actual count in the downloaded CSV file. |

### GCP Existing File Flow (TC07 → TC10)

| Test Case | Description |
|---|---|
| **TC07** | Login, select an existing GCP bucket file via `Cloud Storage → Google Cloud Platform → Existing`, scan the `testing` folder, validate the file, complete the ingestion wizard (File Setup → Config → Ingest), and deploy the pipeline. |
| **TC08** | Open the Monitor module. Create a new batch for the domain, search for it, open task details, and poll until all tasks reach `Completed` (30 min max, 15s polling). |
| **TC09** | Navigate to the Data Lakehouse Workflow module. Dynamically read attribute values and business key column from the uploaded file. Create a DQ rule, configure the Business Key, deploy the pipeline. Validate Data Quality and Data Lake layer task status in the Monitor module. |
| **TC10** | Navigate to the Derived module. Search for the workflow, select it from the left panel, click `+ New Derive`, configure the entity, map 6 columns (Column 1 with Business Key enabled), save, and deploy. Validate the Derived task in the Monitor module. |

---

## TC10 – Derived Module Step Reference

| Step | Action |
|---|---|
| 1 | Open the Derived module from the left navigation |
| 2 | Search for the workflow created in TC07 |
| 3 | Click the workflow from the search results grid |
| 4 | Click the workflow in the left panel, verify `+ New Derive` is enabled, and click it |
| 6 | Enter the auto-generated entity name |
| 7 | Click `+ ADD NEW SOURCE` |
| 9 | Open the **Source Entity** dropdown and select the domain name |
| 10 | Click Next |
| 11 | Enable the PS checkbox |
| 12 | Click Draw Diagram and wait for completion |
| 13 | Select Column 1 from the `source_col_*` dropdown and enable Business Key → click Create |
| 14 | Click `+ ADD NEW`, select Column 2 (no Business Key) → click Create |
| 15 | Repeat for Columns 3–6 (no Business Key). Click Save Changes. Click Deploy Pipeline. |
| 20 | Navigate to the Monitor module |
| 21 | Select Data Lakehouse tab |
| 22 | Search using the domain name from TC07 |
| 23 | Validate domain is present in the results grid |
| 24 | Click the Task button to open task details |
| 25 | Poll the `derived` layer status until `Completed` (30 min max, 15s polling) |

---

## Key Framework Features

### Single Browser Session
- The browser opens **once** per test suite run.
- The same browser instance is shared across all test cases within a flow (TC07 → TC10).
- Login occurs only once; session cookies and tokens are preserved.
- The browser closes only after the full suite completes or immediately upon failure.

### State Persistence via `run_info.json`
- After TC07, the workflow name, file name, and domain name are persisted to `run_info.json`.
- Downstream test cases (TC08–TC10) read this file to dynamically reference the correct domain without hardcoding.
- When running a test case in isolation, `run_info.json` is preserved so the test can read prior state.

### Dynamic File Handling (`utils/file_reader.py`)
- TC09 dynamically resolves the uploaded CSV file path from `report/test_data/` or `test_data/`.
- The attribute value for DQ rule configuration (Step 12) is read directly from the file's first data row.
- The Business Key column (Step 15) is determined from the first column header of the CSV — no hardcoding.

### Robust Polling Strategy
All long-running backend tasks use an active polling loop with:
- **Maximum wait:** 30 minutes (1800 seconds)
- **Poll interval:** 15 seconds
- **Grid refresh:** The refresh button is clicked programmatically before each status check to force the Kendo UI grid to re-fetch data.
- **Console logging:** Every status change is logged, making it easy to trace execution in live output.
- **Immediate exit:** As soon as a target status is reached, polling stops — no unnecessary waiting.

### Failure Handling & Downstream Blocking
```text
TC07 PASS
TC08 PASS
TC09 FAILED
    ↓
TC10 BLOCKED
```
- If any test case fails, all downstream test cases in the same flow are **immediately marked as BLOCKED**.
- Execution stops at the point of failure.

### Evidence Generation
**On Pass:**
- High-resolution DOM screenshots are captured after every step.
- A DOCX evidence report is generated with step-by-step results and screenshots.
- Saved to: `reports/execution_reports/TC{N}_PASSED_{timestamp}.docx`

**On Failure:**
- Screenshots for all completed steps are included up to the failure point.
- An explicit **Failure Screenshot** is captured at the exact moment of the assertion failure.
- Network request/response payloads (BiDi) are captured for the 2 steps before, the failed step, and 2 steps after.
- Saved to: `reports/execution_reports/TC{N}_FAILED_{timestamp}.docx`

---

## How to Execute

### Step 1: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 2: Activate the Environment
```powershell
.\venv\Scripts\activate
```

### Step 3: Install Dependencies *(first time only)*
```powershell
pip install -r requirements.txt
```

### Step 4: Configure the Environment
Create a `.env` file in the project root (if not already present) with the application URL and credentials:
```env
APP_URL=https://your-dataparq-app-url.com
USERNAME=your_username
PASSWORD=your_password
```

### Step 5: Run the Tests

**Run the Full GCP Flow (TC07 → TC10)**
```powershell
.\venv\Scripts\python.exe -m pytest tests/gcp --gcp-file-name=tvs_sales1_data1
```

**Run the Full Manual Upload Flow (TC01 → TC06)**
```powershell
.\venv\Scripts\python.exe -m pytest tests/manual --upload-file=test_data/your_file.csv
```

**Run a Single Test Case (Standalone)**
```powershell
# TC07 only
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc07_gcp_bucket_file_selection.py --gcp-file-name=tvs_sales1_data1

# TC08 only (requires run_info.json from TC07)
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc08_Verify_upload_file_in_Monitor_Module.py --gcp-file-name=tvs_sales1_data1

# TC09 only (requires run_info.json from TC07/TC08)
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc09_data_lakehouse_workflow.py --gcp-file-name=tvs_sales1_data1

# TC10 only (requires run_info.json from TC07–TC09)
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc10_derived_module.py --gcp-file-name=tvs_sales1_data1
```

> **Note:** When running a test case in isolation, `run_info.json` is automatically preserved by the framework so downstream tests can read the workflow and domain name set by TC07.

---

## CLI Arguments Reference

| Argument | Used In | Description |
|---|---|---|
| `--gcp-file-name` | TC07–TC10 | File name (without path) that exists in the GCP `testing/` bucket folder. Extension `.csv` is optional. |
| `--upload-file` | TC01–TC06 | Relative path to the local CSV file to upload (e.g., `test_data/my_file.csv`). |

---

## Reports Directory

All test artifacts are written to the `reports/` directory, which is **automatically cleaned and recreated** at the start of every test run.

```text
reports/
├── execution_reports/
│   ├── TC07_PASSED_20260723_120000.docx
│   ├── TC08_PASSED_20260723_120500.docx
│   ├── TC09_FAILED_20260723_123000.docx   
│   └── Suite_Summary_Report.txt            
├── documents/
│   └── rejected_records_*.csv              
├── screenshots/
│   └── PASS_01.png, FAIL_09.png, ...
└── test_data/
    └── tvs_sales1_data1.csv                
```
