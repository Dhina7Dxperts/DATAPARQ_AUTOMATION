# DataParq Automation - Test Requirements Document

## 1. Overview
This document outlines the business requirements and technical testing steps for the automated end-to-end (E2E) workflow pipeline on the DataParq platform. 

The scope of this automation covers:
- Dynamic file uploading and pipeline deployment.
- Data governance structural validation and re-upload workflows.
- Business Data Quality (DQ) rule configuration.
- End-to-end task execution monitoring within the Data Lakehouse.
- Rejected record payload extraction and file-level verification.

---

## 2. Global Execution Rules
- **Session Continuity:** The automation must reuse a single authenticated browser session across sequential test cases to mimic realistic user behavior and optimize execution time.
- **Fail-Fast Enforcement:** If a dependent test case fails, the subsequent validation test cases must abort immediately without executing, reporting a skipped or BLOCKED state.
- **Dynamic Waiting:** Hardcoded sleep statements are prohibited for backend processing. Polling mechanisms (up to 30 minutes) must be used for file validation and task monitoring.
- **Reporting:** All steps must generate visual evidence (screenshots) and aggregate into a `.docx` execution report alongside Network JSON captures for failures.

---

## 3. Test Cases

### Test Case 1 (TC1): File Upload Flow
**Objective:** Verify that a user can upload a structured dataset, configure entity/ingest details, and successfully deploy the data pipeline.

**Execution Steps:**
1. Log into the DataParq application.
2. Navigate to **ParQ Your Data** > **Data Lakehouse** and click **Create New**.
3. Select the **Governance** tab and upload a dynamically provided dataset (passed via CLI arguments).
4. Complete the **File Setup** (validate Metadata and Sample Data tabs).
5. Complete the **Config** setup by assigning a Data Owner and Data Steward.
6. Complete the **Ingest** setup by entering dynamic Domain/Workflow names, selecting Monthly frequency, and saving.
7. Click **Deploy Pipeline** and capture the success message.
8. Write the dynamically generated Workflow Name to a persistent `run_info.json` file for downstream consumption.

**Expected Outcome:**
The file uploads successfully, configurations are saved, the pipeline is deployed without errors, and the Workflow Name is preserved.

---

### Test Case 2 (TC2): Validation Flow
**Objective:** Verify that the dataset uploaded in TC1 can be re-uploaded in the Data Governance module and undergoes structural validation successfully.

**Execution Steps:**
1. Navigate to the **Data Governance** module.
2. Open the **Upload** section and search for the dynamically generated Workflow Name from TC1.
3. Upload the exact same file used in TC1.
4. Click the **Validate** button to trigger backend structural validation.
5. Poll the UI continuously (every 15 seconds) for up to 30 minutes until the validation success signal ("Rejected Records summary" or success banner) appears.
6. Submit the validated file.
7. Verify the historical upload status reflects the submission.

**Expected Outcome:**
The system successfully validates the file structure within the 30-minute timeout window and permits successful submission.

---

### Test Case 3 (TC3): Monitor Validation
**Objective:** Verify that the backend data processing tasks associated with the uploaded file successfully execute and transition to a "Completed" state.

**Execution Steps:**
1. Navigate to the **Monitor** module.
2. Select the **Data Lakehouse** view via the radio button.
3. Search for the TC1 Workflow Name using the multi-strategy domain search (case-insensitive).
4. Verify the domain is present in the grid results.
5. Navigate to the **Actions** column for that specific row and click the **Task** button (List icon).
6. On the Task Execution page, verify that at least one task row (`k-master-row`) is present in the grid.
7. Monitor the **Status** column badge (`aria-colindex=3`) for all tasks using a long-polling strategy:
   - **Polling Interval:** 30 seconds
   - **Maximum Wait:** 30 minutes

**Expected Outcome:**
Every task successfully transitions to a `Completed` status within 30 minutes. The test will explicitly fail if any task enters `Failed`, `Error`, or `Aborted`.

---

### Test Case 4 (TC4): Business DQ Configuration
**Objective:** Verify the ability to create, configure, and deploy a custom Business Data Quality (DQ) rejection rule on the existing workflow.

**Execution Steps:**
1. Navigate to **ParQ Your Data** > **Data Lakehouse** and click **View All**.
2. Search for the TC1 Workflow Name and open its **Profile** details.
3. Click the **Add / Modify Rules** button.
4. Configure a new rule:
   - **DQ Rule:** Business DQ
   - **DQ Action:** Rejection
   - **Notification:** Enabled
   - **Attribute & Operator:** Select the first attribute and use the `=` operator.
   - **Value:** Dynamically extract a valid non-null value from the uploaded CSV file.
5. Click **Create** and proceed to the Secure page.
6. Dynamically parse the CSV file and explicitly select the **first column** as the **Business Key**. (Ensure Mask and PII configurations remain untouched).
7. Save the Business Key configuration and proceed.
8. Click **Deploy Pipeline**.

**Expected Outcome:**
The Business DQ rule is successfully created with a dynamically fetched value, the first column is configured as the Business Key, and the updated pipeline is deployed successfully.

---

### Test Case 5 (TC5): Pipeline Monitoring
**Objective:** Verify that the newly deployed pipeline (which now includes the Business DQ rule) successfully executes both the Data Lake and Data Quality layers.

**Execution Steps:**
1. Navigate to the **Monitor** module.
2. Select the **Data Lakehouse** view and search for the TC1 Workflow Name.
3. Verify the domain is present in the grid results.
4. Click the **Task** button to open task details.
5. Identify the tasks associated with the `datalake` and `dataquality` layers.
6. Validate that both specific layer tasks reach a `Completed` status.

**Expected Outcome:**
The monitoring grid confirms that the downstream Data Quality layer and Data Lake layer both executed and completed successfully.

---

### Test Case 6 (TC6): Rejected Record Validation
**Objective:** Perform deep-level data integrity validation by ensuring the rejected records caught by the TC4 DQ rule accurately match between the UI and the physical download file.

**Execution Steps:**
1. Navigate to the **Data Governance** module > **Upload** section.
2. Search for the TC1 Workflow Name and upload the exact same file.
3. Click **Validate** and wait dynamically (up to 30 mins) for the backend to process the Business DQ rule.
4. Extract the **Rejected Records Count** displayed in the UI summary.
5. Click the **Download Rejected** button to retrieve the CSV payload.
6. Parse the downloaded CSV file locally and count the total number of data rows.
7. Perform a strict comparison between the UI Rejected Count and the physical CSV Row Count.

**Expected Outcome:**
The validation process successfully identifies rejected records based on the TC4 rule, and the numerical count shown in the UI matches the exact row count of the downloaded CSV file perfectly.
