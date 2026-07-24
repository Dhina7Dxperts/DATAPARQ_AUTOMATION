# DataParQ Automation Framework

## Project Overview

This project automates the end-to-end testing of the **DataParQ** platform using Selenium WebDriver, PyTest, and the Page Object Model (POM) design pattern.

The automation covers **two independent but sequential test flows**:

- **Manual Upload Flow (TC01 → TC06):** Covers the full lifecycle of a manually uploaded CSV file — from ingestion and governance to monitoring, DQ rule creation, and rejected records validation.
- **GCP Existing File Flow (TC07 → TC11):** Covers the full lifecycle of a file sourced from a GCP bucket — from ingestion and monitoring through the Derived module (TC10) and the Enrichment module (TC11).

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.12+ |
| Automation Tool | Selenium WebDriver 4.22 (ChromeDriver) |
| Testing Framework | PyTest 8.0 |
| Design Pattern | Page Object Model (POM) |
| Reporting | `python-docx` (DOCX evidence reports) |
| Data Handling | CSV, JSON |
| Logging | Python `logging` module (custom logger via `utils/logger.py`) |
| Environment Config | `python-dotenv` (`.env` file) |

---

## Project Structure

```text
dataparq_automation/
│
├── pages/                                      # Page Object Model classes
│   ├── login_page.py                           # Login form interactions
│   ├── home_page.py                            # Dashboard / home navigation
│   ├── file_setup_page.py                      # File Setup wizard page
│   ├── config_page.py                          # Config page (Data Owner, Steward)
│   ├── ingest_page.py                          # Ingest page (Domain, Workflow, Schedule)
│   ├── data_lakehouse_page.py                  # Data Lakehouse — file upload & GCP source selection
│   ├── data_lakehouse_workflow_page.py         # DQ Rules, Business Key, pipeline deployment
│   ├── data_governance_page.py                 # Data Governance upload, validate, submit
│   ├── derive_page.py                          # Derived Module entity, column mapping
│   ├── enrichment_page.py                      # Enrichment Module — entity creation, columns, deploy
│   ├── monitor_page.py                         # Monitor Module — batch, task polling, status validation
│   └── task_page.py                            # Task Details page helpers
│
├── tests/
│   ├── manual/                                 # TC01–TC06: Manual upload flow
│   │   ├── test_tc01_file_upload.py
│   │   ├── test_tc02_data_governance.py
│   │   ├── test_tc03_Verify_upload_file_in_Monitor_Module.py
│   │   ├── test_tc04_data_lakehouse_workflow.py
│   │   ├── test_tc05_validate_task_status.py
│   │   └── test_tc06_validate_dq_rejected_records.py
│   │
│   └── gcp/                                    # TC07–TC11: GCP bucket file flow
│       ├── test_tc07_gcp_bucket_file_selection.py
│       ├── test_tc08_Verify_upload_file_in_Monitor_Module.py
│       ├── test_tc09_data_lakehouse_workflow.py
│       ├── test_tc10_derived_module.py
│       └── test_tc11_enrichment.py
│
├── utils/
│   ├── config.py                               # Loads BASE_URL, PARQ_USERNAME, PARQ_PASSWORD from .env
│   ├── file_reader.py                          # CSV reading utilities (attribute values, headers)
│   ├── logger.py                               # Custom logging setup (console + file)
│   ├── network_capture.py                      # BiDi network request/response capture
│   ├── report_generator.py                     # DOCX evidence report generator
│   └── screenshot_manager.py                   # Per-step screenshot capture (PASS_01.png / FAIL_01.png)
│
├── test_data/                                  # Local CSV test files
│   ├── it_company_employee_data.csv
│   ├── tvs_sales1_data3.csv
│   └── sample.csv
│
├── reports/                                    # All generated test artifacts (auto-created)
│   ├── execution_reports/                      # DOCX evidence reports + Suite_Summary_Report.txt
│   ├── documents/                              # Downloaded files (e.g., rejected_records_*.csv)
│   ├── runs/                                   # Per-test-run screenshot folders (timestamped)
│   └── test_data/                              # CSV files copied during GCP flow for validation
│
├── run_info.json                               # Shared state between test cases (domain, workflow, file)
├── conftest.py                                 # Fixtures, failure hooks, report generation, blocking logic
├── pytest.ini                                  # Pytest configuration (order, logging, CLI options)
├── requirements.txt                            # Python package dependencies
└── .env                                        # Environment variables (not committed to source control)
```

---

## Test Case Execution Flow

### Manual Upload Flow (TC01 → TC06)

| TC | Steps | Description |
|---|---|---|
| **TC01** | 30 | Login → Navigate to Data Lakehouse → Upload CSV locally → File Setup (Metadata + Sample Data validation) → Config (Data Owner + Data Steward) → Ingest (Domain Name, Workflow Name, Monthly schedule, Expected Runtime, Notify on Delay) → Deploy Pipeline |
| **TC02** | 10 | Navigate to Data Governance → Upload same CSV file → Validate (File Validated Successfully) → Submit (File Submitted Successfully) → Confirm Historical Upload Status |
| **TC03** | 8 | Monitor → Data Lakehouse view → Search domain (from TC01) → Create New Batch → Confirm → Open Task Details → Poll all tasks to `Completed` (30 min max, 15s interval) |
| **TC04** | 18 | Data Lakehouse Workflow → Search workflow → Click Profile icon → Add/Modify DQ Rule (Business DQ / Rejection / Notification) → Select Attribute + Comparison Operator + Attribute Value → Business Key column → Deploy Pipeline |
| **TC05** | 6 | Monitor → Data Lakehouse view → Search domain → Open Task Details → Poll `dataquality` and `datalake` layers to `Completed` (30 min max, 15s interval) |
| **TC06** | 10 | Data Governance → Upload file → Validate → Capture UI Rejected Count → Download Rejected CSV (JS click to preserve auth tokens) → Assert UI count == CSV row count exactly |

---

### GCP Existing File Flow (TC07 → TC11)

| TC | Steps | Description |
|---|---|---|
| **TC07** | 39 | Login → Cloud Storage → GCP → Existing → Scan `testing/` folder → Select **exact file** via `--gcp-file-name` CLI argument → File Setup (Metadata + Sample Data) → Config (Data Owner + Steward) → Ingest (Domain, Workflow, Monthly schedule, Notify on Delay) → Deploy Pipeline → Persist `workflow_name`, `file_path`, `gcp_file_name` to `run_info.json` |
| **TC08** | 12 | Monitor → Data Lakehouse → Search domain (from TC07) → Create New Batch → Confirm → Re-search → Open Task Details → Poll all tasks to `Completed` (30 min max, 15s interval) |
| **TC09** | 25 | Data Lakehouse Workflow → Search workflow → Click Profile → Add DQ Rule (Business DQ / Rejection) → **Dynamically** read attribute value from CSV first data row → **Dynamically** determine Business Key from CSV first column header → Deploy Pipeline → Monitor → Poll `dataquality` + `datalake` to `Completed` → Validate record counts (DQ Count & Lake Count must be strictly less than Staging Count) |
| **TC10** | 26 | Derived Module → Search workflow → New Derive → Auto-generate Entity Name → Add Source → Select Domain + Workflow + Source Entity → Next → Enable PS checkbox → Draw Diagram → Map 6 columns (Column 1 with Business Key, Columns 2–6 without) → Save Changes → Deploy Pipeline → Monitor → Data Lakehouse → Poll `derived` layer to `Completed` (30 min max, 15s interval) |
| **TC11** | 35 | Enrichment Module → Search domain → Select domain + workflow → Create New Enrichment Entity (name, process, data owner, Historical Data Change Management) → Add 3 Enrichment Columns (Integer/Free Text; String/Static Dropdown; String/Dynamic Dropdown) → Validate All Columns + Enrich views → Save Changes → Drag & Drop reorder → Deploy Pipeline → Monitor → Search domain → Exact match Domain + Workflow in grid → Open Task Details → Poll exactly **2 Enrich layer tasks** to `Completed` (30 min max, 15s interval) |

---

## Step Detail Reference

### TC10 – Derived Module

| Step | Action |
|---|---|
| 1 | Open the Derived module from the left navigation |
| 2 | Search for the workflow created in TC07 |
| 3 | Click the workflow from the search results grid |
| 4 | Click the workflow in the left panel, verify `+ New Derive` is enabled, click it |
| 5 | Click the New Derived button |
| 6 | Generate and enter the auto-formatted entity name |
| 7 | Click `+ Add New Source` |
| 8 | Open **Domain Name** dropdown → select exact domain |
| 9 | Open **Workflow Name** dropdown → select exact workflow |
| 10 | Open **Source Entity** dropdown → select available entity |
| 11 | Click Next |
| 12 | Enable the **PS** checkbox |
| 13 | Click **Draw Diagram** → wait for completion |
| 14 | Select Column 1 in New Column Mapping → enable Business Key → Create |
| 15 | Click `+ Add New` → select Column 2 (no Business Key) → Create |
| 16 | Repeat for Columns 3–6 (no Business Key) → Save Changes → Deploy Pipeline |
| 21 | Navigate to Monitor module |
| 22 | Select Data Lakehouse view |
| 23 | Search using domain name (from TC07) |
| 24 | Validate domain presence in grid |
| 25 | Open Task Details (click Task button for exact row) |
| 26 | Poll `derived` layer → must reach `Completed` within 30 minutes |

---

### TC11 – Enrichment Module

| Step | Action |
|---|---|
| 1 | Open Enrichment module from the left navigation |
| 2 | Enter domain name (from TC07) in search box |
| 3 | Click exact matching domain in the grid |
| 4 | Click the workflow in the left Workflows panel |
| 5 | Click `+ Create New` button |
| 6 | Select the Data Entity created in TC10 from the dropdown |
| 7 | Enter Enrichment Entity Name (format: `test_<domain_name>_enrich`) |
| 8 | Enter Process Name (same as Step 7) |
| 9 | Select Data Owner (`shreyas.senthilkumar@7dxperts.com`) |
| 10 | Enable Historical Data Change Management checkbox |
| 11 | Click Next |
| 12 | Click `+ Add New Column` → enter Column Display Name `sample_1_enrich` |
| 13 | Open Data Type → select **Integer** |
| 14 | Open Column Type → select **Free Text** |
| 15 | Click Add New → verify first column created |
| 16 | Click `+ Add New Column` → enter Column Display Name `sample_2_enrich` |
| 17 | Open Data Type → select **String** |
| 18 | Open Column Type → select **Dropdown** |
| 19 | Select **Static** → enter `sample_data` in Dropdown List input |
| 20 | Click Add New → verify second column created |
| 21 | Click `+ Add New Column` → enter Column Display Name `sample_3_enrich` |
| 22 | Open Data Type → select **String** |
| 23 | Open Column Type → select **Dropdown** |
| 24 | Select **Dynamic** option → verify enabled |
| 25 | Click Add New → verify third column created |
| 26 | Click **All Columns** radio → verify all 3 columns visible in grid |
| 27 | Click **Enrich** radio → verify only enrichment columns shown |
| 28 | Click **Save Changes** → verify success toast |
| 29 | Validate **Drag & Drop** column reorder → verify success toast |
| 30 | Click **Deploy Pipeline** → verify `"SUCCESS: Your changes have been successfully deployed."` toast |
| 31 | Navigate to **Monitor** module (expand Observe & Ask menu if collapsed) |
| 32 | Search using domain name from TC07 |
| 33 | Validate exact match of Domain Name + Workflow Name in grid |
| 34 | Click **Task** button for the exact matching row only |
| 35 | Poll exactly **2 Enrich layer tasks** → both must reach `Completed` (30 min max, 15s interval) |

---

## Key Framework Features

### Single Browser Session
- The browser opens **once** per suite run and is shared across all test cases in the same flow.
- Login occurs only once; session cookies and auth tokens are fully preserved between test cases.
- The browser closes only after the full suite completes or immediately upon a failure.

### State Persistence via `run_info.json`
- TC07 writes `workflow_name`, `file_name`, `file_path`, `gcp_file_name`, and `tc7_status` to `run_info.json`.
- All downstream test cases (TC08–TC11) read this file dynamically so no values are hardcoded.
- Running a test case in isolation is supported — the existing `run_info.json` is preserved.

### Dynamic File Handling (`utils/file_reader.py`)
- TC04 and TC09 dynamically resolve the uploaded CSV path from `reports/test_data/` or `test_data/`.
- The DQ rule **attribute value** is read from the first data row of the CSV file.
- The **Business Key column** is determined from the first column header of the CSV — no hardcoding.

### Kendo UI Interaction Strategy
- Kendo dropdowns, radio buttons, and grids are interacted with via `driver.execute_script(...)` to handle Kendo's custom shadow-like component rendering that blocks standard Selenium click/find.
- Drag-and-drop column reordering (TC11 Step 29) uses `ActionChains` with `click_and_hold` → `move_to_element_with_offset` → `release`.
- Download buttons in SPAs (TC06 Step 10) are clicked via JavaScript click to preserve the application's auth token interceptor.

### Robust Polling Strategy
All long-running backend task validations use an active polling loop with:
- **Maximum wait:** 30 minutes (1800 seconds)
- **Poll interval:** 15 seconds
- **Grid refresh:** The Kendo grid refresh button is clicked programmatically before each status check to force a re-fetch.
- **Status logging:** Every poll cycle and every status change is logged with elapsed time.
- **Terminal states:** Immediately fails on `Failed`, `Error`, `Stopped`, `Cancelled`, or `Aborted`.
- **Immediate exit:** Stops polling as soon as the target status (`Completed`) is reached.
- **TC11 Enrich-specific:** Validates that **exactly 2** Enrich layer tasks exist before polling their status.

### Failure Handling & Downstream Blocking
```
TC07  PASS
TC08  PASS
TC09  FAILED
   ↓
TC10  BLOCKED
TC11  BLOCKED
```
- If any test case fails, all downstream test cases in the same flow are immediately marked as **BLOCKED** in `run_info.json`.
- Execution halts at the point of failure (`-x` flag in `pytest.ini`).

### Evidence Generation

**On Pass:**
- Screenshots are captured after every step (named `PASS_01.png`, `PASS_02.png`, etc.) in a timestamped folder under `reports/runs/`.
- A formatted DOCX evidence report is generated with step-by-step descriptions, expected results, actual results, and embedded screenshots.
- Saved to: `reports/execution_reports/TC{N}_PASSED_{timestamp}.docx`

**On Failure:**
- All screenshots from successfully completed steps are preserved.
- An explicit **Failure Screenshot** is captured at the moment of the assertion (`FAIL_NN.png`).
- Network BiDi request/response payloads are captured in a JSON sidecar file.
- Saved to: `reports/execution_reports/TC{N}_FAILED_{timestamp}.docx`

**Suite Summary:**
- A plain-text `Suite_Summary_Report.txt` is written at session end, listing PASS / FAIL / BLOCKED counts per TC and paths to all evidence documents.

---

## Environment Setup

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
Create a `.env` file in the project root:
```env
BASE_URL=https://gcp.dataparq.com
PARQ_USERNAME=your_username
PARQ_PASSWORD=your_password
```

> **Note:** The environment variable names must be exactly `BASE_URL`, `PARQ_USERNAME`, and `PARQ_PASSWORD` as defined in `utils/config.py`.

---

## How to Execute Tests

### Run Full GCP Flow (TC07 → TC11)
```powershell
.\venv\Scripts\python.exe -m pytest tests/gcp --gcp-file-name=tvs_sales1_data4
```

### Run Full Manual Upload Flow (TC01 → TC06)
```powershell
.\venv\Scripts\python.exe -m pytest tests/manual --upload-file=test_data/it_company_employee_data.csv
```

### Run Individual GCP Test Cases
```powershell
# TC07 only — creates run_info.json for downstream tests
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc07_gcp_bucket_file_selection.py --gcp-file-name=tvs_sales1_data1

# TC08 only — requires run_info.json from TC07
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc08_Verify_upload_file_in_Monitor_Module.py --gcp-file-name=tvs_sales1_data1

# TC09 only — requires run_info.json from TC07/TC08
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc09_data_lakehouse_workflow.py --gcp-file-name=tvs_sales1_data1

# TC10 only — requires run_info.json from TC07–TC09
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc10_derived_module.py --gcp-file-name=tvs_sales1_data3

# TC11 only — requires run_info.json from TC07–TC10
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc11_enrichment.py --gcp-file-name=tvs_sales1_data1
```

### Run Individual Manual Test Cases
```powershell
# TC01 only
.\venv\Scripts\python.exe -m pytest tests/manual/test_tc01_file_upload.py --upload-file=test_data/it_company_employee_data.csv

# TC06 only — requires run_info.json from TC01–TC05
.\venv\Scripts\python.exe -m pytest tests/manual/test_tc06_validate_dq_rejected_records.py --upload-file=test_data/it_company_employee_data.csv
```

> **Note:** When running a test case in isolation, `run_info.json` from a prior run is automatically preserved, so downstream tests can still read the workflow and domain names set by TC07 or TC01.

---

## CLI Arguments Reference

| Argument | Used In | Description |
|---|---|---|
| `--gcp-file-name` | TC07–TC11 | File name (without `.csv` extension) that exists inside the GCP `testing/` bucket folder. The `.csv` extension is appended automatically. |
| `--upload-file` | TC01–TC06 | Relative path to the local CSV file to upload (e.g., `test_data/it_company_employee_data.csv`). |

---

## Reports Directory Layout

```text
reports/
├── execution_reports/
│   ├── TC07_PASSED_20260724_120000.docx
│   ├── TC08_PASSED_20260724_120500.docx
│   ├── TC09_FAILED_20260724_123000.docx
│   ├── TC11_PASSED_20260724_175500.docx
│   └── Suite_Summary_Report.txt            # Overall PASS/FAIL/BLOCKED summary
│
├── documents/
│   └── rejected_records_*.csv              # Downloaded by TC06
│
├── runs/
│   └── test_tc11_enrichment_20260724_175000/
│       ├── PASS_01.png
│       ├── PASS_02.png
│       └── FAIL_30.png                     # Only present on failure
│
└── test_data/
    └── tvs_sales1_data1.csv                # CSV copied during GCP flow
```

---

## Page Object Summary

| Page Class | Module | Key Responsibilities |
|---|---|---|
| `LoginPage` | `pages/login_page.py` | Login form, credential submission |
| `HomePage` | `pages/home_page.py` | Left nav menu, module navigation |
| `DataLakehousePage` | `pages/data_lakehouse_page.py` | Upload area, GCP source selection, folder scan, exact file checkbox selection |
| `FileSetupPage` | `pages/file_setup_page.py` | Metadata tab, Sample Data tab, Next button |
| `ConfigPage` | `pages/config_page.py` | Data Owner, Data Steward, Save, success validation |
| `IngestPage` | `pages/ingest_page.py` | Domain Name, Workflow Name, Workflow Type, Schedule, Expected Runtime, Notify on Delay, Deploy |
| `DataLakehouseWorkflowPage` | `pages/data_lakehouse_workflow_page.py` | View All, Profile icon, DQ Rule modal, Business Key configuration, Deploy Pipeline |
| `DataGovernancePage` | `pages/data_governance_page.py` | Upload, Validate, Submit, Rejected Record Count capture, Download Rejected CSV (JS click) |
| `DerivePage` | `pages/derive_page.py` | Search, New Derive, Entity Name, Add Source (Domain/Workflow/Entity), Column Mapping (with/without Business Key), Save, Deploy |
| `EnrichmentPage` | `pages/enrichment_page.py` | Create Entity (name, process, data owner), Add Enrichment Columns (Free Text / Static Dropdown / Dynamic Dropdown), Validate views, Save Changes, Drag & Drop reorder, Deploy Pipeline |
| `MonitorPage` | `pages/monitor_page.py` | Navigate (auto-expand Observe & Ask), Data Lakehouse radio, search, Create Batch, click Task button (exact match), status polling for single/multiple/enrich layers, record count validation |
| `TaskPage` | `pages/task_page.py` | Task Details page helpers |
