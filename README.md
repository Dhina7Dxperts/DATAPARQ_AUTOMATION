# DataParQ Automation Framework

## Project Overview
This project automates the end-to-end testing of the DataParQ Databricks Embedded Analytics flow using Selenium, PyTest, and the Page Object Model (POM) framework.

The automation validates the complete workflow from data onboarding to data quality validation and rejected record verification.

## Framework Details
### Technology Stack
- **Language:** Python
- **Automation Tool:** Selenium WebDriver (ChromeDriver)
- **Testing Framework:** PyTest
- **Design Pattern:** Page Object Model (POM)
- **Data Manipulation:** Pandas, OpenPyXL, CSV
- **Reporting & Evidence Generation:** python-docx

### Recent Enhancements & Fixes
The framework has been heavily optimized for stability, particularly with long-running backend processes and complex UI grids:
- **Dynamic Asynchronous Waiting:** 
  - *Data Governance Validation (TC2/TC6):* Polls for validation completion up to **30 minutes** (checking every 15 seconds), proceeding immediately once the UI indicates success (no hardcoded waits).
  - *Monitor Task Execution (TC3/TC5):* Polls task execution grid up to **30 minutes** (checking every 30 seconds), explicitly failing if any task hits a terminal failure state.
- **Robust UI Interactions (Kendo Grids):**
  - *Multi-Strategy Search:* Uses a 4-layer fallback strategy for interacting with complex search boxes and Kendo grids (testing popups, JS events, direct ENTER key inputs, and scanning unfiltered grids).
  - *Case-Insensitive XPath Matching:* Utilizes `translate()` in XPath to ensure workflows and domains are successfully matched regardless of how the UI renders text casing.
- **TC4 Business Key Configuration:** Dynamically parses the uploaded CSV file and strictly sets the *first column* as the Business Key, leaving Mask and PII configurations untouched.
- **Enhanced Failure Reporting:** Network capture logs now safely generate internal directories before saving (`os.makedirs`), ensuring you always get the `Request.json` and `Response.json` payloads upon any step failure.

## Project Structure
```text
dataparq_automation/
├── pages/                  # Page Object Model classes
├── tests/                  # PyTest test cases (TC1 to TC6)
├── test_data/              # Input CSV files and payloads
├── utils/                  # Helper utilities (ScreenshotManager, NetworkCapture)
├── reports/                # Automatically generated during execution
│   ├── execution_reports/  # Generated DOCX/PDF evidence and JSON logs
│   ├── documents/          # Downloaded verification files (e.g., CSVs)
│   └── screenshots/        # Temporary storage for step-by-step images
├── pytest.ini              # PyTest configuration (enforces strict ordering)
├── conftest.py             # Global fixtures, hooks, and session management
└── README.md
```

## Test Case Execution Flow
The framework contains six sequentially dependent test cases:

**TC1 → TC2 → TC3 → TC4 → TC5 → TC6**

Execution always rigidly follows this ascending order.

### Dependency Rules
- **TC2** executes only if **TC1** passes.
- **TC3** executes only if **TC2** passes.
- **TC4** executes only if **TC3** passes.
- **TC5** executes only if **TC4** passes.
- **TC6** executes only if **TC5** passes.

### Failure Handling
If any test case fails, execution stops immediately and all downstream tests are marked as **BLOCKED**.

*Example:*
```text
TC1 PASS
TC2 PASS
TC3 FAILED
 ↓
TC4 BLOCKED
TC5 BLOCKED
TC6 BLOCKED
```

## Browser Execution Strategy
The framework is deeply optimized to use a **single browser session**:
- The browser opens exactly **once** before TC1 starts.
- The identical browser instance is reused across TC1 through TC6.
- Login occurs only once; cookies, tokens, and session state are fully preserved across all test cases.
- The browser closes only after TC6 completes successfully, or immediately if a failure triggers a test suite abort.

## Implemented Test Cases

### TC1: End-to-end Data Onboarding
Validates the foundational data ingestion and workflow configuration module.
- **Step 1:** Login to the application and verify Dashboard loads
- **Step 2:** Navigate to ParQ Your Data and verify Data Lakehouse section is visible
- **Step 3:** Click Create New inside Data Lakehouse and verify Choose Source page loads
- **Step 4:** Select Governance tab and verify upload area is visible
- **Step 5:** Upload the file and verify — fail if app shows an error (e.g., unsupported format)
- **Step 6:** Verify Next button is enabled after upload and navigate to File Setup page
- **Step 7:** Validate Metadata tab — verify table and rows are populated
- **Step 8:** Validate Sample Data tab — verify data rows are populated
- **Step 9:** Verify Next button is enabled on File Setup page and click it
- **Step 10:** Verify navigation to Config page — Entity Level Setup visible
- **Step 11:** Validate Entity Level Setup section and Source Entities panel are visible
- **Step 12:** Verify Save button is disabled before selecting Data Owners and Data Stewards
- **Step 13:** Select Data Owner and verify selection
- **Step 14:** Select Data Steward and verify selection
- **Step 15:** Verify Save button is enabled after selections and click Save
- **Step 16:** Verify success message 'Config updated successfully' is displayed
- **Step 17:** Verify Next button is enabled after save and click it
- **Step 18:** Verify navigation to Ingest page
- **Step 19:** Select 'Create New' radio button in Add to Data Domain Group
- **Step 20:** Verify Save button is disabled before filling mandatory Ingest fields
- **Step 21:** Enter Domain Name (dynamic: filename without extension)
- **Step 22:** Enter Workflow Name (same as Domain Name)
- **Step 23:** Select Workflow Type: Monthly
- **Step 24:** Enter Expected Runtime (M): 5
- **Step 25:** Enable Notify on Delay checkbox
- **Step 26:** Verify Save button is enabled after all fields filled and click Save
- **Step 27:** Verify save success message: 'Schedule data is saved successfully'
- **Step 28:** Verify Deploy Pipeline button is enabled after save
- **Step 29:** Click Deploy Pipeline button
- **Step 30:** Verify deployment success message is displayed

### TC2: Data Governance Re-upload Validation
Ensures data governance files can be uploaded and structurally validated prior to ingestion.
- **Step 1:** Navigate to Data Governance
- **Step 2:** Open Upload Section
- **Step 3:** Search for Workflow Created in TC1
- **Step 4:** Upload Same File Again
- **Step 5:** Validate Validate Button Behavior
- **Step 6:** Validate Uploaded File (Dynamic Wait up to 30 mins)
- **Step 7:** Validate Submit Button Behavior
- **Step 8:** Submit File
- **Step 9:** Validate Historical Upload Status

### TC3: Upload Verification in Monitor Module
Validates that the submitted data workflow properly transitions to a completed state in the monitoring layer.
- **Step 1:** Navigate to the Monitor module
- **Step 2:** Select Data Lakehouse Option
- **Step 3:** Search Using Domain Name from TC1 (Case-insensitive)
- **Step 4:** Validate Domain Presence in results grid
- **Step 5:** Click the Task button in the Actions column
- **Step 6:** Identify All Tasks
- **Step 7:** Validate Task Count >= 1
- **Step 8:** Monitor Status Transition to Completed (Dynamic Poll up to 30 mins)

### TC4: Data Lakehouse Workflow Deployment
Tests the creation and deployment of custom Data Quality (DQ) rules onto the data pipeline.
- **Step 1:** Navigate to ParQ Your Data
- **Step 2:** Click 'View All' in Data Lakehouse section
- **Step 3:** Search Workflow
- **Step 4:** Validate Workflow Presence
- **Step 5:** Click the Profile Icon for the Selected Flow
- **Step 6:** Click the 'Add / Modify Rules' Button
- **Step 7:** Select DQ Rule as 'Business DQ'
- **Step 8:** Select DQ Action as 'Rejection'
- **Step 9:** Enable Notification
- **Step 10:** Select Attribute
- **Step 11:** Select Comparison Operator
- **Step 12:** Enter Attribute Value (Dynamically extracted from CSV data)
- **Step 13:** Click Create
- **Step 14:** Click the Next Button
- **Step 15:** Select Business Key Column (Dynamically selects strictly the 1st column of the CSV)
- **Step 16:** Save the Business Key Configuration
- **Step 17:** Click the Next Button After Saving Business Key
- **Step 18:** Deploy the Pipeline and Verify Successful Deployment

### TC5: Validate Data Quality and Lakehouse Task Status
Ensures the downstream data quality processing reaches completion in the monitoring module.
- **Step 1:** Open the Monitor Module
- **Step 2:** Select Data Lakehouse
- **Step 3:** Enter Domain Name
- **Step 4:** Verify Domain Appears in Grid
- **Step 5:** Open Task Details
- **Step 6:** Validate Only Data Quality and Data Lake Layer Status

### TC6: Validate DQ Rejected Records Count
Performs deep-level validation that the rejected records matched against the DQ rule in TC4 are accurately parsed and available for download.
- **Step 1:** Open Data Governance Module
- **Step 2:** Open Upload Section
- **Step 3:** Search Workflow Name
- **Step 4:** Validate Workflow Exists
- **Step 5:** Open Workflow
- **Step 6:** Upload File
- **Step 7:** Click Validate (Waits dynamically for asynchronous backend verification)
- **Step 8:** Capture Validation Summary (Extracts rejected counts from UI)
- **Step 9:** Store Rejected Record Count
- **Step 10:** Validate Downloaded Rejected Records File (Directly intercepts the downloaded CSV and strictly compares file row count with the UI payload)

## Automatic Evidence Generation
### Passed Test Cases
For every passed test case:
- Captures high-resolution DOM screenshots for every executed step.
- Automatically generates an evidence report in DOCX format.
- Saves the evidence document under: `reports/execution_reports/`

### Failed Test Cases
If a test case fails:
- Captures screenshots for all successful steps up to the point of failure.
- Captures an explicit **Failure Screenshot** at the exact moment the assertion fails.
- Automatically captures **Request and Response network payloads** exclusively for the failed step to assist debugging (avoids unnecessary execution overhead on passed steps).
- Drops the Failure Screenshot and JSON Network payloads directly into `reports/execution_reports/`.

## Rejected File Handling & Verification
Downloaded rejected records (CSV files) are natively intercepted by the framework and automatically stored securely in:
`reports/documents/`

The framework enforces strict data integrity by validating that the:
1. Rejected count shown in the UI.
2. Rejected count physically present in the downloaded CSV file.

**Both values must match identically for TC6 to pass.**


---

## How to Execute

### Step 1: Create a Fresh Virtual Environment
*Isolate your project dependencies by creating a new virtual environment.*
```powershell
python -m venv venv
```

### Step 2: Activate the Environment
*Activate the virtual environment to ensure the correct Python executable is used.*
```powershell
.\venv\Scripts\activate
```

### Step 3: Install the Blueprint (Dependencies)
*Install the required libraries to run the tests. (First time only)*
```powershell
pip install -r requirements.txt
```

### Step 4: Execute the Tests!
*Run the full test suite in sequence.*
```powershell
.\venv\Scripts\python.exe -m pytest --upload-file=test_data/abc_company_sales_data_fixed.csv
```

---

#### 🎯 Option 2: Run a Specific Test Case (e.g., just TC1)
*If you need to debug or run an individual test case, use the command below.*
```powershell
.\venv\Scripts\python.exe -m pytest tests\test_tc01_file_upload.py --upload-file=test_data\ipl_match_data.csv
```
