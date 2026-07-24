# DataParq Automation – Test Requirements Document

## 1. Overview

This document outlines the business requirements and technical testing steps for the automated end-to-end (E2E) workflow pipeline on the DataParq platform.

The scope covers two independent execution flows:

- **Manual Upload Flow (TC01 → TC06):** Tests the complete data onboarding pipeline by manually uploading a CSV file from the local system — from ingestion through governance, monitoring, DQ rule configuration, and rejected record validation.
- **GCP Existing File Flow (TC07 → TC11):** Tests the complete pipeline by selecting a file that already exists in a Google Cloud Platform (GCP) bucket, followed by monitoring, DQ rule creation, Derived module pipeline creation, Enrichment module entity creation, and task monitoring.

---

## 2. Global Execution Rules

| Rule | Description |
|---|---|
| **Intelligent Login** | `login_if_needed()` is used by all TCs. It performs login only when the authenticated app is not already active — detected via presence of known sidebar elements. This allows a single login for the entire suite while remaining standalone-safe. |
| **Session Continuity** | A single browser session (`scope="session"`) is shared across all test cases in the same flow. The browser closes only after the last TC completes or upon a critical failure. |
| **Fail-Fast Enforcement** | If any TC fails, all downstream TCs in the same flow are immediately marked `BLOCKED` in `run_info.json`. Execution stops at the failure point (`-x` flag). |
| **State Persistence** | Workflow Name, domain name, file name, and file path generated in TC01/TC07 are written to `run_info.json`. All downstream TCs must read this file dynamically — no hardcoded names permitted. |
| **Dynamic Waiting** | Hard-coded `sleep()` calls are prohibited for backend operations. Active polling (up to 30 minutes, 15-second interval) with Kendo UI grid refresh before every status check is required. |
| **Screenshots** | A screenshot is captured after every step, named `PASS_NN.png` or `FAIL_NN.png`, and stored in a timestamped folder under `reports/runs/`. |
| **Evidence Reporting** | All steps aggregate into a `.docx` execution report per TC. On failure, Chrome DevTools Protocol (CDP) network logs (Request + Response JSON) are captured via `utils/network_capture.py`. |
| **Standalone Execution** | Any individual TC (TC01–TC11) must be executable in isolation. `run_info.json` is preserved between runs to allow downstream TCs to read prior state. |

---

## 3. Test Cases

### 3.1 Manual Upload Flow (TC01 → TC06)

---

#### TC01 – File Upload & Pipeline Deployment
**Objective:** Verify that a user can manually upload a structured CSV dataset from the local machine, configure entity and ingest details, and successfully deploy the data pipeline.

**Pre-conditions:** A valid local CSV file is provided via CLI argument `--upload-file`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Login to the application via `login_if_needed()`. Verify dashboard loads. | Dashboard loads; login skipped if session already active. |
| 2 | Navigate to **ParQ Your Data** → **Data Lakehouse**, click **Create New**. | Data Lakehouse section visible. |
| 3 | Click **Create New** to open the Choose Source page. | Choose Source page loads. |
| 4 | Select the **Governance** upload tab. | Upload area becomes visible. |
| 5 | Upload the local CSV file. Fail if the app shows an unsupported format error. | File uploads without errors. |
| 6 | Verify **Next** is enabled after upload, click it to navigate to File Setup. | File Setup page loads. |
| 7 | Validate **Metadata** tab — table and rows are populated. | Metadata rows are visible. |
| 8 | Validate **Sample Data** tab — data rows are populated. | Sample data rows are visible. |
| 9 | Verify **Next** is enabled on File Setup, click it. | Config page loads. |
| 10 | Verify navigation to Config page — Entity Level Setup is visible. | Entity Level Setup heading is visible. |
| 11 | Validate Entity Level Setup section and Source Entities panel are visible. | Both panels visible. |
| 12 | Verify **Save** button is disabled before selecting Data Owner and Steward. | Save button is disabled. |
| 13 | Select Data Owner: `deepanraj.thangaraj@7dxperts.com`. | Data Owner selected. |
| 14 | Select Data Steward: `shreyas.senthilkumar@7dxperts.com`. | Data Steward selected. |
| 15 | Verify **Save** is now enabled, click it. | Config saves. |
| 16 | Verify success message: *"Config updated successfully"*. | Toast message appears. |
| 17 | Verify **Next** is enabled, click it. | Ingest page loads. |
| 18 | Verify navigation to Ingest page. | Ingest page confirmed. |
| 19 | Select **Create New** radio button in Add to Data Domain Group. | Radio button selected. |
| 20 | Verify **Save** is disabled before filling mandatory Ingest fields. | Save button is disabled. |
| 21 | Enter **Domain Name** (dynamic: filename without extension). | Domain Name entered. |
| 22 | Enter **Workflow Name** (same as Domain Name). | Workflow Name entered. |
| 23 | Select **Workflow Type: Monthly**. | Monthly selected. |
| 24 | Enter **Expected Runtime (M): 5**. | Runtime entered. |
| 25 | Enable **Notify on Delay** checkbox. | Checkbox enabled. |
| 26 | Verify **Save** is enabled, click it. | Schedule saves. |
| 27 | Verify success message: *"Schedule data is saved successfully"*. | Toast message appears. |
| 28 | Verify **Deploy Pipeline** button is enabled. | Button is enabled. |
| 29 | Click **Deploy Pipeline**. | Deployment initiates. |
| 30 | Verify deployment success message is displayed. | Success toast appears. |

**Post-conditions:** Workflow Name and file path are persisted to `run_info.json` (`tc1_status = "PASS"`).

---

#### TC02 – Data Governance Validation
**Objective:** Verify that the dataset uploaded in TC01 can be submitted through the Data Governance module and undergoes structural validation successfully.

**Pre-conditions:** TC01 must have passed. `run_info.json` must contain `workflow_name` and `tc1_status = "PASS"`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Data Governance** module. | Page loads successfully. |
| 2 | Open the Upload section. | Upload area visible. |
| 3 | Search for the Workflow Name from TC01. | Workflow name entered. |
| 4 | Select the exact matching workflow from the search results. | Exact workflow selected. |
| 5 | Upload the same local CSV file used in TC01. | File uploads without errors. |
| 6 | Verify **Validate** button is initially disabled, then enabled after upload; click it. | Validation triggered. |
| 7 | Poll until success message *"File Validated Successfully"* appears (30 min max). | Validation succeeds. |
| 8 | Verify **Submit** button is initially disabled, then enabled after validation; click it. | Submission triggered. |
| 9 | Verify success message *"File Submitted Successfully"* appears. | Submission confirmed. |
| 10 | Verify the Historical Upload Status reflects a successful submission. | Status updated. |

**Post-conditions:** `run_info.json` updated with `tc2_status = "PASS"`.

---

#### TC03 – Monitor Task Validation (Manual Flow)
**Objective:** Verify that the backend data processing tasks for TC01 execute and transition to `Completed`.

**Pre-conditions:** TC02 must have passed. `run_info.json` must contain `tc2_status = "PASS"` and `workflow_name`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Monitor** module. | Monitor page loads. |
| 2 | Select the **Data Lakehouse** view. | View selected. |
| 3 | Search for the Domain Name from TC01 (read dynamically from `run_info.json`). | Search term entered. |
| 4 | Validate the domain appears in the results grid. | Domain visible in grid. |
| 5 | Click the **Task** button for that domain row. | Task details page opens. |
| 6 | Verify at least one task row is present. | Task count ≥ 1. |
| 7 | Verify task count is ≥ 1. | Count confirmed. |
| 8 | Poll all task statuses every 15 seconds (up to 30 minutes) until all reach `Completed`. Trigger a Kendo UI grid refresh before each poll. Fail immediately on terminal states (`Failed`, `Error`, `Aborted`). | All tasks `Completed`. |

**Post-conditions:** `run_info.json` updated with `tc3_status = "PASS"`.

---

#### TC04 – Business DQ Configuration (Manual Flow)
**Objective:** Verify creation, configuration, and deployment of a custom Business DQ rejection rule on the TC01 workflow.

**Pre-conditions:** TC03 must have passed. `run_info.json` must contain `tc3_status = "PASS"` and `workflow_name`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to **ParQ Your Data** (home module). | Page loads. |
| 2 | Click **View All** under the Data Lakehouse section. | Workflow list page opens. |
| 3 | Search for the TC01 Workflow Name. | Search returns results. |
| 4 | Validate the workflow is present in the grid. | Workflow visible. |
| 5 | Click the **Profile** icon for that workflow. | Flow details page opens. |
| 6 | Click **Add / Modify Rules**. | DQ rule modal opens. |
| 7 | Set **DQ Rule** to `Business DQ`. | Business DQ selected. |
| 8 | Set **DQ Action** to `Rejection`. | Rejection selected. |
| 9 | Enable the **Notification** toggle. | Notification enabled. |
| 10 | Select the first available attribute column. | Attribute selected. |
| 11 | Set the comparison operator to `=`. | Operator set. |
| 12 | Dynamically read the first non-null value for the attribute from the CSV (via `utils/file_reader.py`) and enter it. | Attribute value entered. |
| 13 | Click **Create** to save the rule. | Rule created successfully. |
| 14 | Click **Next** to navigate to the Secure (Business Key) page. | Secure page opens. |
| 15 | Dynamically read the first column name from the CSV (via `utils/file_reader.py`) and select it as the **Business Key**. | Business Key selected. |
| 16 | Click **Save** on the Secure page. | Business Key saved. |
| 17 | Click **Next** to proceed. | Next page loads. |
| 18 | Click **Deploy Pipeline** and verify the success message. | Pipeline deployed. |

**Post-conditions:** `run_info.json` updated with `tc4_status = "PASS"`.

---

#### TC05 – Pipeline Monitoring – Post-DQ (Manual Flow)
**Objective:** Verify that the pipeline deployed in TC04 (with the Business DQ rule) executes and completes both the Data Lake and Data Quality layers.

**Pre-conditions:** TC04 must have passed. `run_info.json` must contain `tc4_status = "PASS"`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Monitor** module. | Monitor page loads. |
| 2 | Select the **Data Lakehouse** view. | View selected. |
| 3 | Search for the Domain Name from TC01. | Domain found. |
| 4 | Validate the domain is present in the grid. | Domain visible. |
| 5 | Click the **Task** button to open task details. | Task details open. |
| 6 | Poll every 15 seconds (up to 30 minutes) until both `dataquality` and `datalake` layer tasks reach `Completed`. Kendo grid is refreshed before each poll. | Both layers `Completed`. |

**Post-conditions:** `run_info.json` updated with `tc5_status = "PASS"`.

---

#### TC06 – Rejected Record Validation
**Objective:** Validate that the rejected record count shown in the UI matches the count in the physically downloaded CSV file.

**Pre-conditions:** TC05 must have passed. `run_info.json` must contain `tc5_status = "PASS"`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to **Data Governance** module. | Page loads. |
| 2 | Open the Upload section. | Upload area visible. |
| 3 | Search for the TC01 Workflow Name. | Workflow found. |
| 4 | Select the exact matching workflow. | Workflow selected. |
| 5 | Upload the same local CSV file from TC01. | Upload succeeds. |
| 6 | Click **Validate** and poll until validation completes (30 min max). | Validation succeeds. |
| 7 | Capture the **Rejected Records Count** displayed in the UI. | Count stored. |
| 8 | Store the rejected count for comparison. | Count captured. |
| 9 | Click **Download Rejected** (via JS click to preserve the SPA auth-token interceptor). Poll `reports/documents/` for the downloaded CSV to appear (60 sec max). | CSV file downloaded. |
| 10 | Parse the downloaded CSV, count data rows, and assert UI count == CSV row count exactly. | Counts match. |

**Post-conditions:** `run_info.json` updated with `tc6_status = "PASS"`.

> **Note:** The Download Rejected button uses a JavaScript click (`execute_script`) rather than a direct link navigation, to ensure the SPA's authentication token interceptor fires correctly and the API request includes the required Bearer token.

---

### 3.2 GCP Existing File Flow (TC07 → TC11)

---

#### TC07 – GCP Bucket File Selection & Pipeline Deployment
**Objective:** Verify that a user can select a dataset that already exists in a GCP bucket, configure entity and ingest details, and successfully deploy the data pipeline.

**Pre-conditions:** File name is provided via CLI argument `--gcp-file-name`. File must exist in the GCP `testing/` folder under the `landing_zone` connection.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Login via `login_if_needed()`. Verify dashboard loads. | Login completes or is skipped if session active. |
| 2 | Navigate to **ParQ Your Data** → **Data Lakehouse**. | ParQ module loads. |
| 3 | Click **Create New** inside Data Lakehouse. | Choose Source page loads. |
| 4 | Select **Cloud Storage** → **Google Cloud Platform** → **Existing**. | GCP option selected. |
| 5 | Select the `landing_zone` connection. | Connection selected. |
| 6 | Enter folder name `testing`. | Folder entered. |
| 7 | Select **Each file is an entity** and click **Scan**. | Scan results appear. |
| 8 | Select the checkbox for the exact file matching `--gcp-file-name` (exact match). | File checkbox selected. |
| 9 | Click **Next** to proceed to File Setup. | File Setup page loads. |
| 10 | Validate **Metadata** tab — table and rows populated. | Metadata rows visible. |
| 11 | Validate **Sample Data** tab — data rows populated. | Sample data rows visible. |
| 12 | Click **Next** on File Setup. | Config page loads. |
| 13 | Validate Entity Level Setup section and Source Entities panel visible. | Both panels visible. |
| 14 | Verify **Save** disabled before selections. | Save disabled. |
| 15 | Select Data Owner: `deepanraj.thangaraj@7dxperts.com`. | Data Owner selected. |
| 16 | Select Data Steward: `shreyas.senthilkumar@7dxperts.com`. | Data Steward selected. |
| 17 | Verify **Save** enabled, click it. Verify success: *"Config updated successfully"*. | Config saved. |
| 18 | Click **Next** to navigate to Ingest. | Ingest page loads. |
| 19 | Select **Create New** radio button in Add to Data Domain Group. | Radio selected. |
| 20 | Verify **Save** disabled before filling mandatory fields. | Save disabled. |
| 21–25 | Enter Domain Name (dynamic), Workflow Name, Workflow Type: Monthly, Expected Runtime: 5, enable Notify on Delay. | All fields filled. |
| 26 | Click **Save**. Verify: *"Schedule data is saved successfully"*. | Schedule saved. |
| 27–28 | Verify **Deploy Pipeline** enabled, click it. | Deployment initiates. |
| 29 | Verify deployment success message. | Success toast appears. |
| 30–39 | Persist `workflow_name`, `file_name`, `file_path`, `gcp_file_name` and `tc7_status = "PASS"` to `run_info.json`. | State saved. |

**Post-conditions:** `run_info.json` written with all workflow identifiers.

---

#### TC08 – Monitor Validation (GCP Flow)
**Objective:** Verify that the backend data processing tasks for TC07 execute and transition to `Completed`.

**Pre-conditions:** TC07 must have passed. `run_info.json` must contain `tc7_status = "PASS"` and `workflow_name`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Monitor** module. | Monitor page loads. |
| 2 | Select the **Data Lakehouse** view. | View selected. |
| 3 | Search for the Workflow Name from TC07 (dynamic). | Search term entered. |
| 4 | Validate the domain is present in the grid. | Domain visible. |
| 5 | Click the **`+` (Create Batch)** icon for that domain row. | Batch creation dialog appears. |
| 6 | Click **Yes** to confirm batch creation. | Batch creation begins. |
| 7 | Search for the Workflow Name again to refresh the grid. | Search re-entered. |
| 8 | Validate exact domain presence in the refreshed grid. | Exact match visible. |
| 9 | Click the **Task** button to open task details. | Task details page opens. |
| 10 | Verify at least one task row is present. | Task count ≥ 1. |
| 11 | Verify task count ≥ 1. | Count confirmed. |
| 12 | Poll all task statuses every 15 seconds (up to 30 minutes) until all reach `Completed`. Kendo grid refreshed before each poll. | All tasks `Completed`. |

**Post-conditions:** `run_info.json` updated with `tc8_status = "PASS"`.

---

#### TC09 – Data Lakehouse Workflow – DQ Rule & Pipeline
**Objective:** Verify that a Business DQ rejection rule is created on the GCP workflow, the Business Key column is dynamically set, the pipeline is deployed, and both Data Quality and Data Lake task layers reach `Completed` in Monitor. Validate record counts.

**Pre-conditions:** TC08 must have passed. `run_info.json` must contain `workflow_name` and `gcp_file_name`.

**Execution Steps:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to **ParQ Your Data**. | Page loads. |
| 2 | Click **View All** under Data Lakehouse. | Workflow list opens. |
| 3 | Search for the Workflow Name from TC07. | Search returns results. |
| 4 | Validate the workflow appears in the grid. | Workflow visible. |
| 5 | Click the **Profile** icon to open workflow details. | Details page opens. |
| 6 | Click **Add / Modify Rules**. | Rule modal opens. |
| 7 | Set **DQ Rule** to `Business DQ`. | Business DQ selected. |
| 8 | Set **DQ Action** to `Rejection`. | Rejection selected. |
| 9 | Enable **Notification**. | Notification enabled. |
| 10 | Select the first available attribute column. | Attribute selected. |
| 11 | Set comparison operator to `=`. | Operator set. |
| 12 | Dynamically read the first non-null value for the attribute from the CSV (via `utils/file_reader.py`) and enter it. | Value entered. |
| 13 | Click **Create** to save the rule. | Rule created. |
| 14 | Click **Next** to navigate to the Secure page. | Secure page opens. |
| 15 | Dynamically read the first column name from the CSV (via `utils/file_reader.py`) and select it as **Business Key**. | Business Key selected. |
| 16 | Click **Save** on the Secure page. | Business Key saved. |
| 17 | Click **Next** to proceed. | Next page loads. |
| 18 | Click **Deploy Pipeline** and verify success message. | Pipeline deployed. |
| 19 | Navigate to the **Monitor** module. | Monitor page loads. |
| 20 | Select the **Data Lakehouse** view. | View selected. |
| 21 | Search for the TC07 Domain Name. | Domain found. |
| 22 | Validate exact domain presence in grid. | Exact match visible. |
| 23 | Click **Task** button to open task details. | Task details open. |
| 24 | Poll every 15 seconds (up to 30 minutes) until both `Data Quality` and `Data Lake` layers reach `Completed`. Kendo grid refreshed before each poll. | Both layers `Completed`. |
| 25 | Validate that **DQ Count** and **Data Lake Count** are strictly less than **Staging Count**. | Count integrity confirmed. |

**Post-conditions:** `run_info.json` updated with `tc9_status = "PASS"`.

---

#### TC10 – Derived Module – Entity Creation & Pipeline
**Objective:** Verify the end-to-end Derived entity creation flow: select the workflow, create a derived entity with 6 column mappings, deploy the pipeline, and validate the Derived task reaches `Completed` in Monitor.

**Pre-conditions:** TC09 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**

**Derived Entity Setup:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Derived** module from the left navigation. | Derived page opens. |
| 2 | Search for the Workflow Name from TC07. | Workflow appears in grid. |
| 3 | Click the workflow from the search results grid. | Workflow clicked. |
| 4 | In the left panel, click the workflow to highlight it, verify `+ New Derive` is enabled, and click it. | New Derive form opens. |
| 5 | Click the **New Derived** button to open the form. | Form opens. |
| 6 | Generate and enter the entity name (format: `test_{workflow_name}_derive`). | Entity Name entered. |
| 7 | Click **`+ ADD NEW SOURCE`**. | Source modal opens. |
| 8 | Open the **Domain Name** dropdown and select the exact domain. | Domain selected. |
| 9 | Open the **Workflow Name** dropdown and select the exact workflow. | Workflow selected. |
| 10 | Open the **Source Entity** dropdown and select the available entity. | Source Entity selected. |
| 11 | Click **Next** in the Add Source modal. | Next step proceeds. |
| 12 | Enable the **PS** checkbox (`input#primary_source_1`). | PS enabled. |
| 13 | Click **Draw Diagram** and wait until diagram generation completes. | Diagram generated. |

**Column Mapping:**

| Step | Action | Expected Result |
|---|---|---|
| 14 | Locate the column dropdown, select **Column 1**, enable **Business Key** (`input#isBusinesskey`), click **Create**. | Column 1 created with Business Key. |
| 15 | Click **`+ Add New`**, select **Column 2**, do NOT enable Business Key, click **Create**. | Column 2 created. |
| 16 | Repeat for **Columns 3, 4, 5, 6** — do NOT enable Business Key for any. Click **Save Changes**, then click **Deploy Pipeline**. | All columns created; pipeline deployed. |

**Business Key Rule:**

| Column | Business Key |
|---|---|
| Column 1 | ✅ Enabled |
| Column 2 | ❌ Disabled |
| Column 3 | ❌ Disabled |
| Column 4 | ❌ Disabled |
| Column 5 | ❌ Disabled |
| Column 6 | ❌ Disabled |

**Monitor Validation:**

| Step | Action | Expected Result |
|---|---|---|
| 21 | Navigate to the **Monitor** module. | Monitor page loads. |
| 22 | Select the **Data Lakehouse** view. | View selected. |
| 23 | Search using the Domain Name from TC07. | Domain found. |
| 24 | Validate the domain is present in the grid. | Domain visible. |
| 25 | Click the **Task** button for the matching domain row. | Task details open. |
| 26 | Poll every 15 seconds (up to 30 minutes) until the `derived` layer task reaches `Completed`. Kendo grid refreshed before each poll. | Derived task `Completed`. |

**Post-conditions:** `run_info.json` updated with `tc10_status = "PASS"`.

---

#### TC11 – Enrichment Module – Entity Creation, Column Configuration & Pipeline
**Objective:** Verify the full Enrichment module flow: create an enrichment entity with 3 enrichment columns of different types, validate column views, reorder via drag-and-drop, deploy the pipeline, and validate exactly 2 Enrich layer tasks reach `Completed` in Monitor.

**Pre-conditions:** TC10 must have passed. `run_info.json` must contain `workflow_name`.

**Execution Steps:**

**Enrichment Entity Setup:**

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to the **Enrichment** module from the left navigation. | Enrichment page opens with search box visible. |
| 2 | Enter the Domain Name (from TC07) in the search box. | Matching domain appears in the grid. |
| 3 | Click the exact matching domain in the grid. | Domain selected. |
| 4 | In the left-side Workflows panel, click the workflow associated with the domain. | Workflow selected. |
| 5 | Verify the **`+ Create New`** button becomes enabled, click it. | Create New Enrichment Entity dialog appears. |
| 6 | From the Data Entity dropdown, select the entity created in TC10. | Data Entity selected. |
| 7 | Enter the **Enrichment Entity Name** in the format: `test_<domain_name>_enrich`. | Name entered. |
| 8 | Enter the **Process Name** (same value as Step 7). | Process Name entered. |
| 9 | Open the **Data Owners** dropdown and select `shreyas.senthilkumar@7dxperts.com`. | Data Owner selected. |
| 10 | Check the **Historical Data Change Management** (Type 2) checkbox. | Checkbox enabled. |
| 11 | Click the **Next** button and verify navigation to the enrichment column configuration page. | Column configuration page loads. |

**First Enrichment Column (`sample_1_enrich`):**

| Step | Action | Expected Result |
|---|---|---|
| 12 | Click **`+ Add New Column`**. Verify the Create Enrichment Column dialog opens. Enter Column Display Name: `sample_1_enrich`. | Dialog opens; name entered. |
| 13 | Open the **Data Type** dropdown and select **Integer**. | Integer selected. |
| 14 | Open the **Column Type** dropdown and select **Free Text**. | Free Text selected. |
| 15 | Click **Add New**. Verify the first enrichment column is created successfully. | Column `sample_1_enrich` created. |

**Second Enrichment Column (`sample_2_enrich`):**

| Step | Action | Expected Result |
|---|---|---|
| 16 | Click **`+ Add New Column`**. Verify dialog opens. Enter Column Display Name: `sample_2_enrich`. | Dialog opens; name entered. |
| 17 | Open the **Data Type** dropdown and select **String**. | String selected. |
| 18 | Open the **Column Type** dropdown and select **Dropdown**. | Dropdown type selected. |
| 19 | Select the **Static** radio option. Enter `sample_data` in the Dropdown List textbox. Verify the value is entered. | Static selected; value entered. |
| 20 | Click **Add New**. Verify the second enrichment column is created. | Column `sample_2_enrich` created. |

**Third Enrichment Column (`sample_3_enrich`):**

| Step | Action | Expected Result |
|---|---|---|
| 21 | Click **`+ Add New Column`**. Verify dialog opens. Enter Column Display Name: `sample_3_enrich`. | Dialog opens; name entered. |
| 22 | Open the **Data Type** dropdown and select **String**. | String selected. |
| 23 | Open the **Column Type** dropdown and select **Dropdown**. | Dropdown type selected. |
| 24 | Select the **Dynamic** radio option. Verify it is enabled. | Dynamic option enabled. |
| 25 | Click **Add New**. Verify the third enrichment column is created. | Column `sample_3_enrich` created. |

**Column View Validation:**

| Step | Action | Expected Result |
|---|---|---|
| 26 | Click the **All Columns** radio button. Wait for the table to refresh. Verify that `sample_1_enrich`, `sample_2_enrich`, and `sample_3_enrich` are all present in the grid (exact match). | All 3 enrichment columns visible. |
| 27 | Click the **Enrich** radio button. Wait for the table to refresh. Verify that **only** the enrichment columns are displayed, each appearing exactly once. | Only enrichment columns visible. |

**Save, Drag & Drop, and Deploy:**

| Step | Action | Expected Result |
|---|---|---|
| 28 | Click the **Save Changes** button. Verify the success toast appears. | Save succeeds. |
| 29 | Validate **Drag & Drop** column reorder using `ActionChains`. Verify the success toast appears after reorder. | Columns reordered; toast confirmed. |
| 30 | Click the **Deploy Pipeline** button. Verify the success toast: *"SUCCESS: Your changes have been successfully deployed."* | Deployment confirmed. |

**Monitor Validation:**

| Step | Action | Expected Result |
|---|---|---|
| 31 | Navigate to the **Monitor** module (expand **Observe & Ask** section from sidebar if collapsed). | Monitor page loads. |
| 32 | Search using the Domain Name from TC07. | Domain appears in grid. |
| 33 | Validate that the exact Domain Name and Workflow Name match in the grid. | Exact row confirmed. |
| 34 | Click the **Task** button for the exact matching row only. | Task details page opens. |
| 35 | Confirm exactly **2 Enrich layer tasks** are present. Poll every 15 seconds (up to 30 minutes) until both tasks reach `Completed`. Kendo grid refreshed before each poll. | Both Enrich tasks `Completed`. |

**Post-conditions:** `run_info.json` updated with `tc11_status = "PASS"`.

---

## 4. Login Management

The framework uses a unified `login_if_needed()` method in `LoginPage` that implements intelligent login detection:

```
login_if_needed():
    1. Check if authenticated app is already visible (sidebar nav elements present)
       → YES: Skip login (suite mode, session already active)
       → NO: Continue
    2. Navigate to BASE_URL, wait 4 seconds for SPA redirect
    3. Check again for authenticated app indicators
       → YES: Skip login (auth cookie still valid)
       → NO: Continue
    4. Perform full login (enter credentials, submit form, wait for dashboard)
```

**Authentication Indicators (positive detection):**
- `//a[@href='/monitor']`
- `//a[contains(@href, 'parq-your-data')]`
- `//div[contains(@class, 'truncate') and text()='Monitor']`
- `//span[text()='OBSERVE & ASK']`

**Execution Mode Behaviour:**

| Mode | Behaviour |
|---|---|
| Standalone (any TC) | Fresh browser → no indicators → performs full login |
| TC01–TC06 Suite | TC01 logs in; TC02–TC06 detect active session → skip login |
| TC07–TC11 Suite | TC07 logs in; TC08–TC11 detect active session → skip login |

---

## 5. Polling Strategy

All backend status polling follows these rules:

| Parameter | Value |
|---|---|
| Maximum Wait Time | 30 minutes (1800 seconds) |
| Poll Interval | 15 seconds |
| Grid Refresh | Kendo UI refresh button is clicked via JS before every status check |
| Immediate Exit | Polling stops as soon as the target status is reached |
| Terminal Failure States | `Failed`, `Error`, `Stopped`, `Cancelled`, `Aborted` |
| TC11 Enrich Validation | Exactly **2** Enrich layer tasks must be present before polling begins |
| Console Logging | Every poll cycle and every status change is logged with elapsed time |

---

## 6. State File: `run_info.json`

`run_info.json` is a JSON file written and read by the framework to pass state between test cases. It is preserved at the project root between runs to allow standalone TC execution.

**Written by:** TC01 (manual flow) and TC07 (GCP flow)  
**Read by:** TC02–TC06 (manual), TC08–TC11 (GCP)

**Structure (GCP flow example):**
```json
{
  "tc7_status":  "PASS",
  "workflow_name": "tvs_sales1_data3",
  "file_path":  "C:\\...\\reports\\test_data\\tvs_sales1_data3.csv",
  "file_name":  "tvs_sales1_data3.csv",
  "gcp_file_name": "tvs_sales1_data3.csv",
  "tc8_status":  "PASS",
  "tc9_status":  "PASS",
  "tc10_status": "PASS",
  "tc11_status": "PASS"
}
```

**Blocking cascade (written by `conftest.py` on failure):**
- Manual flow: TC`N` fails → TC`N+1` through TC6 marked `BLOCKED`
- GCP flow: TC`N` fails → TC`N+1` through TC11 marked `BLOCKED`

> `run_info.json` is never deleted at session start. It is only overwritten when TC01 or TC07 executes successfully.

---

## 7. Dynamic File Reader (`utils/file_reader.py`)

| Function | Used In | Purpose |
|---|---|---|
| `get_uploaded_file_path(file_name)` | TC04, TC06, TC09 | Searches `reports/test_data/` then `test_data/`. Fails clearly if not found. |
| `get_attribute_value_from_file(file_name, attribute_name)` | TC04 Step 12, TC09 Step 12 | Reads the first non-null value for the given column header from the CSV. Used for DQ rule attribute value. |
| `get_business_key_from_file(file_name)` | TC04 Step 15, TC09 Step 15 | Returns the first column header name. Used to dynamically select the Business Key column. |

---

## 8. Network Capture (`utils/network_capture.py`)

On test failure, Chrome DevTools Protocol (CDP) performance logs are parsed and saved as JSON files for debugging:

| Output | Description |
|---|---|
| `Step_NN_Request.json` | All HTTP requests captured for the failed step |
| `Step_NN_Response.json` | All HTTP responses captured for the failed step |
| Saved to | `reports/network_logs/` |

---

## 9. CLI Arguments Reference

| Argument | Used In | Description |
|---|---|---|
| `--gcp-file-name` | TC07–TC11 | File name (without `.csv` extension) that exists in the GCP `testing/` bucket folder. Extension is auto-appended if missing. |
| `--upload-file` | TC01–TC06 | Relative path to the local CSV file to upload. Default: `test_data/sample.csv`. |
| `--gcp-flow` | Internal | Boolean flag for GCP flow detection (TC07–TC11 scope). |

---

## 10. Execution Commands

### Full GCP Suite (TC07 → TC11)
```powershell
.\venv\Scripts\python.exe -m pytest tests/gcp --gcp-file-name=tvs_sales1_data3
```

### Full Manual Suite (TC01 → TC06)
```powershell
.\venv\Scripts\python.exe -m pytest tests/manual --upload-file=test_data/it_company_employee_data.csv
```

### Individual TC Standalone Execution
```powershell
# TC07 only (creates run_info.json for downstream)
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc07_gcp_bucket_file_selection.py --gcp-file-name=tvs_sales1_data3

# TC08 only
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc08_Verify_upload_file_in_Monitor_Module.py --gcp-file-name=tvs_sales1_data3

# TC09 only
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc09_data_lakehouse_workflow.py --gcp-file-name=tvs_sales1_data3

# TC10 only
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc10_derived_module.py --gcp-file-name=tvs_sales1_data3

# TC11 only
.\venv\Scripts\python.exe -m pytest tests/gcp/test_tc11_enrichment.py --gcp-file-name=tvs_sales1_data3

# TC01 only
.\venv\Scripts\python.exe -m pytest tests/manual/test_tc01_file_upload.py --upload-file=test_data/it_company_employee_data.csv

# TC06 only
.\venv\Scripts\python.exe -m pytest tests/manual/test_tc06_validate_dq_rejected_records.py --upload-file=test_data/it_company_employee_data.csv
```

---

## 11. Reports Directory Layout

```text
reports/
├── execution_reports/
│   ├── TC07_PASSED_20260724_120000.docx
│   ├── TC08_PASSED_20260724_120500.docx
│   ├── TC11_FAILED_20260724_175000.docx
│   └── Suite_Summary_Report.txt
│
├── documents/
│   └── rejected_records_*.csv          ← Downloaded by TC06 Step 9
│
├── runs/
│   └── test_tc11_enrichment_20260724/
│       ├── PASS_01.png ... PASS_35.png
│       └── FAIL_30.png                 ← Only present on failure
│
├── network_logs/
│   └── Step_30_Request.json
│   └── Step_30_Response.json
│
└── test_data/
    └── tvs_sales1_data3.csv            ← Copied from GCP during TC07
```

---

## 12. Page Object Summary

| Page Class | File | TC Usage | Key Responsibilities |
|---|---|---|---|
| `LoginPage` | `login_page.py` | All TCs | Login form, `login_if_needed()`, `is_already_logged_in()` |
| `HomePage` | `home_page.py` | TC01, TC07 | ParQ module navigation, sidebar interaction |
| `DataLakehousePage` | `data_lakehouse_page.py` | TC01, TC07 | Local CSV upload, GCP source selection, folder scan, file checkbox selection |
| `FileSetupPage` | `file_setup_page.py` | TC01, TC07 | Metadata tab, Sample Data tab, Next button |
| `ConfigPage` | `config_page.py` | TC01, TC07 | Data Owner, Data Steward dropdowns, Save, success validation |
| `IngestPage` | `ingest_page.py` | TC01, TC07 | Domain Name, Workflow Name, type, schedule, Notify on Delay, Deploy |
| `DataGovernancePage` | `data_governance_page.py` | TC02, TC06 | Upload, Validate, Submit, rejected count capture, Download Rejected (JS click) |
| `DataLakehouseWorkflowPage` | `data_lakehouse_workflow_page.py` | TC04, TC09 | View All, Profile icon, DQ Rule modal, Business Key, Deploy Pipeline |
| `MonitorPage` | `monitor_page.py` | TC03, TC05, TC08, TC09, TC10, TC11 | Navigate (auto-expand Observe & Ask), Data Lakehouse radio, search, Create Batch, click Task (exact match), multi-layer polling, Enrich layer validation, record count validation |
| `TaskPage` | `task_page.py` | TC03, TC08 | Task details page helpers |
| `DerivePage` | `derive_page.py` | TC10 | Search, New Derive, Entity Name, Add Source (Domain/Workflow/Entity), Column Mapping (with/without Business Key), Save Changes, Deploy Pipeline |
| `EnrichmentPage` | `enrichment_page.py` | TC11 | Search domain, Select domain/workflow, Create Entity, Add Enrichment Columns (Free Text / Static Dropdown / Dynamic Dropdown), Validate All Columns & Enrich views, Save Changes, Drag & Drop reorder, Deploy Pipeline |
