# DataParq Automation - Test Requirements Document

## 1. Overview
This document outlines the business requirements and technical testing steps for the automated end-to-end (E2E) workflow pipeline on the DataParq platform.

The scope of this automation covers two independent execution flows:

- **Manual Upload Flow (TC01 → TC06):** Tests the complete data onboarding pipeline by manually uploading a CSV file from the local system.
- **GCP Existing File Flow (TC07 → TC10):** Tests the complete pipeline by selecting a file that already exists in a Google Cloud Platform (GCP) bucket, followed by DQ rule creation, Derived module pipeline creation, and task monitoring.

---

## 2. Global Execution Rules

- **Session Continuity:** The automation must reuse a single authenticated browser session across sequential test cases within a specific flow (e.g., TC01→TC06, or TC07→TC10) to mimic realistic user behavior and optimize execution time.
- **Fail-Fast Enforcement:** If a test case fails, all subsequent test cases in that flow must be marked as **BLOCKED** and must not execute.
- **State Persistence:** The Workflow Name, domain name, and file name generated in TC07 are written to `run_info.json`. All downstream test cases (TC08–TC10) must read this file dynamically — no hardcoded names are permitted.
- **Dynamic Waiting:** Hardcoded sleep statements are prohibited for backend processing. Active polling mechanisms (up to 30 minutes, 15-second interval) must be used for task monitoring, with a Kendo UI grid refresh triggered before every status check.
- **Reporting:** All steps must generate visual evidence (screenshots) and aggregate into a `.docx` execution report. Upon failure, network payloads (Request/Response JSON via BiDi) must be captured for debugging.
- **Standalone Execution:** Any individual test case must be executable in isolation. If run standalone, the framework must detect the session state and perform login automatically if required. `run_info.json` is preserved between runs for this purpose.

---

## 3. Test Cases

### 3.1 Manual Upload Flow (TC01 → TC06)

#### Test Case 1 (TC01): File Upload Flow
**Objective:** Verify that a user can manually upload a structured dataset from their local machine, configure entity/ingest details, and successfully deploy the data pipeline.

**Pre-conditions:** A valid local CSV file is provided via CLI argument `--upload-file`.

**Execution Steps:**
1. Log into the DataParq application and verify the dashboard loads.
2. Navigate to **ParQ Your Data** > **Data Lakehouse** and click **Create New**.
3. Select the upload source, upload the local CSV file.
4. Complete **File Setup** — validate Metadata and Sample Data tabs.
5. Complete **Config** — assign a Data Owner and Data Steward, save.
6. Complete **Ingest** — enter a dynamically generated Domain Name and Workflow Name, select Monthly frequency (Day: 1st, Expected Runtime: 5), enable Notify on Delay, and save.
7. Click **Deploy Pipeline** and verify the deployment success message.
8. Persist the Workflow Name and file path to `run_info.json` for downstream consumption.

**Expected Outcome:**
The file uploads successfully, configurations are saved, the pipeline deploys without errors, and the Workflow Name is preserved in `run_info.json`.

---

#### Test Case 2 (TC02): Data Governance Validation
**Objective:** Verify that the dataset uploaded in TC01 can be submitted through the Data Governance module and undergoes structural validation successfully.

**Pre-conditions:** TC01 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**
1. Navigate to the **Data Governance** module.
2. Search for the Workflow Name from TC01.
3. Upload the same local file used in TC01.
4. Click **Validate** to trigger backend structural validation.
5. Poll continuously (every 15 seconds, up to 30 minutes) until the validation success banner appears.
6. Submit the validated file.
7. Verify the historical upload status reflects a successful submission.

**Expected Outcome:**
The system validates the file structure within 30 minutes and permits successful submission.

---

#### Test Case 3 (TC03): Monitor Task Validation
**Objective:** Verify that the backend data processing tasks associated with TC01 execute and transition to `Completed`.

**Pre-conditions:** TC02 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**
1. Navigate to the **Monitor** module.
2. Select the **Data Lakehouse** view.
3. Search for the TC01 Workflow Name (dynamic, case-insensitive).
4. Verify the domain is present in the grid.
5. Click the **Task** button for that domain.
6. Verify at least one task row is present.
7. Poll all task statuses every 30 seconds (up to 30 minutes) until all reach `Completed`.

**Expected Outcome:**
All tasks successfully reach `Completed` status. The test explicitly fails if any task enters a terminal failure state (`Failed`, `Error`, `Aborted`).

---

#### Test Case 4 (TC04): Business DQ Configuration
**Objective:** Verify the creation, configuration, and deployment of a custom Business DQ rejection rule on the TC01 workflow.

**Pre-conditions:** TC03 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**
1. Navigate to **ParQ Your Data** > **Data Lakehouse** > **View All**.
2. Search for the TC01 Workflow Name and open its Profile details.
3. Click **Add / Modify Rules**.
4. Configure the rule: DQ Rule = `Business DQ`, DQ Action = `Rejection`, Notification = enabled.
5. Select the first attribute column, set operator to `=`, and dynamically extract a valid non-null value from the uploaded CSV file.
6. Click **Create**.
7. Proceed to the Secure page and dynamically set the **first column** of the CSV as the **Business Key** (Mask and PII columns must remain untouched).
8. Save the Business Key configuration and click **Next**.
9. Click **Deploy Pipeline** and verify the success message.

**Expected Outcome:**
The Business DQ rule is created with a dynamically fetched value, the first column is the Business Key, and the pipeline is redeployed successfully.

---

#### Test Case 5 (TC05): Pipeline Monitoring (Post-DQ)
**Objective:** Verify that the pipeline deployed in TC04 (with the Business DQ rule) executes and completes the Data Lake and Data Quality layers.

**Pre-conditions:** TC04 must have passed.

**Execution Steps:**
1. Navigate to the **Monitor** module and select the **Data Lakehouse** view.
2. Search for the TC01 Workflow Name and verify domain presence.
3. Click the **Task** button to open task details.
4. Identify tasks for the `datalake` and `dataquality` layers.
5. Poll until both specific layer tasks reach `Completed` (15-second interval, 30-minute max).

**Expected Outcome:**
Both the Data Quality and Data Lake layers complete successfully.

---

#### Test Case 6 (TC06): Rejected Record Validation
**Objective:** Validate that the rejected record count shown in the UI matches the count in the physically downloaded CSV file.

**Pre-conditions:** TC05 must have passed.

**Execution Steps:**
1. Navigate to **Data Governance** > **Upload** and search for the TC01 Workflow Name.
2. Upload the same local file from TC01.
3. Click **Validate** and poll until the Business DQ rule produces a Rejected Records summary (up to 30 minutes).
4. Extract the **Rejected Records Count** shown in the UI.
5. Click **Download Rejected** to retrieve the CSV payload.
6. Parse the downloaded CSV and count the data rows.
7. Assert that the UI count equals the CSV row count exactly.

**Expected Outcome:**
The UI rejected count matches the physical CSV row count precisely.

---
---

### 3.2 GCP Existing File Flow (TC07 → TC10)

#### Test Case 7 (TC07): GCP Bucket File Selection & Pipeline Deployment
**Objective:** Verify that a user can select a dataset that already exists in a GCP bucket, configure entity/ingest details, and successfully deploy the data pipeline.

**Pre-conditions:** The file name is provided via CLI argument `--gcp-file-name`. The file must exist in the GCP `testing/` folder under the `landing_zone` connection.

**Execution Steps:**
1. Log into the DataParq application and verify the dashboard loads.
2. Navigate to **ParQ Your Data** > **Data Lakehouse** and click **Create New**.
3. Select **Cloud Storage** > **Google Cloud Platform** > **Existing**.
4. Select the `landing_zone` connection.
5. Enter `testing` as the folder name.
6. Select **Each file is an entity** and click **Scan**.
7. Validate that the expected file (from `--gcp-file-name`) appears in the scan results grid.
8. Click **Next** and complete **File Setup** — validate Metadata and Sample Data tabs are populated.
9. Complete **Config** — select Data Owner (`deepanraj.thangaraj@7dxperts.com`) and Data Steward (`shreyas.senthilkumar@7dxperts.com`), save.
10. Complete **Ingest** — enter a dynamically generated Domain Name (derived from the file name) and Workflow Name, select Monthly frequency (Day: 1st, Expected Runtime: 5 mins), enable Notify on Delay, and save.
11. Click **Deploy Pipeline** and verify the deployment success message.
12. Persist the Workflow Name, GCP file name, and file path to `run_info.json`.

**Expected Outcome:**
The file is successfully selected from the GCP bucket. Configurations are saved, the pipeline is deployed without errors, and all identifiers are persisted to `run_info.json`.

---

#### Test Case 8 (TC08): Monitor Validation (GCP Flow)
**Objective:** Verify that the backend data processing tasks for the TC07 GCP workflow execute and transition to `Completed`.

**Pre-conditions:** TC07 must have passed. `run_info.json` must have `tc7_status = "PASS"` and `workflow_name`.

**Execution Steps:**
1. Navigate to the **Monitor** module.
2. Select the **Data Lakehouse** view.
3. Search for the Workflow Name from TC07 (read dynamically from `run_info.json`).
4. Verify the domain is present in the results grid.
5. Click the **`+` (Create Batch)** icon for that domain row to trigger a new batch.
6. Confirm batch creation by clicking **Yes** on the confirmation dialog.
7. Search for the Workflow Name again to refresh the grid.
8. Validate exact domain presence in the grid.
9. Click the **Task** button to open task details.
10. Verify at least one task row is present.
11. Poll all task statuses every 30 seconds (up to 30 minutes) until all reach `Completed`.

**Expected Outcome:**
A new batch is created successfully and all tasks reach `Completed` status within 30 minutes. The status is saved to `run_info.json` (`tc8_status = "PASS"`).

---

#### Test Case 9 (TC09): Data Lakehouse Workflow – DQ Rule & Pipeline
**Objective:** Verify that a Business DQ rejection rule can be created on the GCP workflow, the Business Key column is set dynamically, the pipeline is deployed, and the resulting Data Quality and Data Lake task layers reach `Completed` in the Monitor module.

**Pre-conditions:** TC08 must have passed. `run_info.json` must contain `workflow_name` and `gcp_file_name`.

**Execution Steps:**
1. Navigate to **ParQ Your Data** and click **View All** under the Data Lakehouse section.
2. Search for the Workflow Name from TC07.
3. Validate that the workflow appears in the grid.
4. Click the **Profile** icon for that workflow to open its details page.
5. Click **Add / Modify Rules** to open the rule configuration modal.
6. Set **DQ Rule** to `Business DQ`.
7. Set **DQ Action** to `Rejection`.
8. Enable **Notification**.
9. Select the **first available attribute** column from the dropdown.
10. Set the comparison operator to `=`.
11. Dynamically read the first non-null value for the selected column from the uploaded CSV file (via `utils/file_reader.py`) and enter it as the attribute value.
12. Click **Create** to save the rule.
13. Click **Next** to navigate to the Secure (Business Key) page.
14. Dynamically read the first column name from the CSV file (via `utils/file_reader.py`) and select it as the **Business Key**. Mask Column and Contain PII columns must not be touched.
15. Click **Save** on the Secure page.
16. Click **Next** to proceed.
17. Click **Deploy Pipeline** and verify the success message.
18. Navigate to the **Monitor** module.
19. Select the **Data Lakehouse** view.
20. Search for the TC07 Workflow Name.
21. Validate exact domain presence in the grid.
22. Click the **Task** button to open task details.
23. Poll every **15 seconds** (up to **30 minutes**) until both the `Data Quality` and `Data Lake` layer tasks reach `Completed` status. Triggers a Kendo grid refresh before each poll.
24. Validate that the DQ and Data Lake record counts are strictly less than the Staging count.

**Expected Outcome:**
The Business DQ rule is successfully created and deployed. Both the Data Quality and Data Lake task layers complete successfully in the Monitor module, and record counts pass integrity validation.

---

#### Test Case 10 (TC10): Derived Module – Entity Creation & Pipeline
**Objective:** Verify the end-to-end Derived entity creation flow: select the workflow, create a derived entity with column mappings, deploy the pipeline, and validate the Derived task reaches `Completed` in the Monitor module.

**Pre-conditions:** TC09 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**

**Derived Entity Setup:**
1. Navigate to the **Derived** module from the left navigation sidebar.
2. Search for the Workflow Name from TC07 in the search box.
3. Click the workflow from the search results grid.
4. Locate the workflow in the left-panel list (below the search box), click it to highlight it, verify the `+ New Derive` button becomes enabled, then click `+ New Derive`.
5. *(Step 5 merged into Step 4 above.)*
6. Enter the auto-generated entity name (format: `test_{workflow_name}_derive`).
7. Click **`+ ADD NEW SOURCE`** (`<span class="text-[11px]">ADD NEW SOURCE</span>`).

**Source Configuration (Add Source Modal):**
9. Open the **Source Entity** dropdown (`label#source_name_label`) and select the domain name. Do NOT interact with the Workflow or Domain Name dropdowns.
10. Click **Next** in the Add Source modal.
11. Enable the **PS** checkbox (`input#primary_source_1`).
12. Click **Draw Diagram** and wait until the diagram generation completes.

**Column Mapping:**
13. *(Step 13 – First Mapping):* Locate the column dropdown (`span[id^="source_col_"]`), select **Column 1**, enable the **Business Key** checkbox (`input#isBusinesskey`), click **Create**.
14. *(Step 14 – Second Mapping):* Click **`+ ADD NEW`**, select **Column 2**, do NOT check Business Key, click **Create**.
15. *(Step 15 – Remaining Mappings):* Repeat for **Column 3, 4, 5, and 6** — do NOT check Business Key for any of them. Click **Create** after each.

**Save & Deploy:**
15. (Continued) Click **Save Changes** and verify the success message. Click **Deploy Pipeline** and verify the success message.

**Monitor Validation:**
20. Navigate to the **Monitor** module.
21. Select the **Data Lakehouse** tab.
22. Search for the Workflow Name from TC07 (dynamic, read from `run_info.json`).
23. Validate that the domain is present in the results grid. If not found, fail with a clear error message.
24. Click the **Task** button to open task details for that domain.
25. Poll every **15 seconds** (up to **30 minutes**) until the `derived` layer task status changes to `Completed`. Triggers a Kendo grid refresh before each poll.

**Business Key Rule:**

| Column   | Business Key |
|----------|-------------|
| Column 1 | ✅ Enabled  |
| Column 2 | ❌ Disabled |
| Column 3 | ❌ Disabled |
| Column 4 | ❌ Disabled |
| Column 5 | ❌ Disabled |
| Column 6 | ❌ Disabled |

**Expected Outcome:**
The Derived entity is successfully created with 6 column mappings (Column 1 as Business Key). The pipeline deploys without errors. The `derived` layer task in the Monitor module reaches `Completed` within 30 minutes.

---

## 4. Polling Strategy

All backend status polling in the automation follows these rules:

| Parameter | Value |
|---|---|
| **Maximum Wait Time** | 30 minutes (1800 seconds) |
| **Poll Interval** | 15 seconds |
| **Grid Refresh** | Kendo UI refresh button is clicked via JS before every status check |
| **Immediate Exit** | Polling stops as soon as the target status is reached |
| **Terminal Failure** | If any layer hits `Failed`, `Error`, or `Aborted`, the test fails immediately |
| **Console Logging** | Every status change is logged to the live console output |

---

## 5. State File: run_info.json

`run_info.json` is a JSON file written and read by the framework to pass state between test cases.

**Written by:** TC07  
**Read by:** TC08, TC09, TC10

**Structure:**
```json
{
  "tc7_status": "PASS",
  "workflow_name": "tvs_sales1_data1",
  "file_path": "C:\\...\\test_data\\sample.csv",
  "file_name": "sample.csv",
  "gcp_file_name": "tvs_sales1_data1.csv",
  "tc8_status": "PASS",
  "tc9_status": "PASS",
  "tc10_status": "PASS"
}
```

> **Note:** `run_info.json` is preserved at the project root between test runs. It is only reset when TC07 executes and writes new values.

---

## 6. Dynamic File Reader (utils/file_reader.py)

The `file_reader.py` utility resolves the uploaded CSV file path dynamically at runtime.

| Function | Purpose |
|---|---|
| `get_uploaded_file_path(file_name)` | Searches `report/test_data/` then `test_data/` for the file. Fails clearly if not found. |
| `get_attribute_value_from_file(file_name, attribute_name)` | Reads the first non-null value for the given column header from the CSV. Used in TC09 Step 12. |
| `get_business_key_from_file(file_name)` | Returns the name of the first column header. Used in TC09 Step 15. |

---

## 7. CLI Arguments Reference

| Argument | Used In | Description |
|---|---|---|
| `--gcp-file-name` | TC07–TC10 | File name (without extension) that exists in the GCP `testing/` folder. Extension `.csv` is auto-appended if missing. |
| `--upload-file` | TC01–TC06 | Relative path to the local CSV file to upload (e.g., `test_data/my_file.csv`). |

---

## 8. Execution Commands

**Full GCP Suite (TC07 → TC10):**
```powershell
.\venv\Scripts\python.exe -m pytest tests/gcp --gcp-file-name=tvs_sales1_data1
```

**Full Manual Suite (TC01 → TC06):**
```powershell
.\venv\Scripts\python.exe -m pytest tests/manual --upload-file=test_data/your_file.csv
```

**Single Test Case (Standalone):**
```powershell
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc10_derived_module.py --gcp-file-name=tvs_sales1_data1
```
