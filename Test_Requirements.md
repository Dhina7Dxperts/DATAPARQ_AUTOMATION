# DataParq Automation - Test Requirements Document

## 1. Overview
This document outlines the business requirements and technical testing steps for the automated end-to-end (E2E) workflow pipeline on the DataParq platform. 

The scope of this automation covers:
- Dynamic file uploading in the Sandbox module.
- Generating and capturing dynamic Domain (Workflow) Names.
- Validating data governance pipelines.
- End-to-end task execution monitoring within the Data Lakehouse.

---

## 2. Global Execution Rules
- **Session Continuity:** The automation must reuse a single authenticated browser session across sequential test cases to mimic realistic user behavior and optimize execution time.
- **Fail-Fast Enforcement:** If a dependent test case fails (e.g., File Upload fails), the subsequent validation test cases (e.g., Monitor or Governance) must abort immediately without executing, reporting a skipped state.
- **Reporting:** All steps must generate visual evidence (screenshots) and aggregate into a `.docx` execution report.

---

## 3. Test Cases

### Test Case 1 (TC1): File Upload Validation
**Objective:** Verify that a user can upload a structured dataset into the DataParq Sandbox and that the system dynamically registers it with a unique Workflow/Domain Name.

**Execution Steps:**
1. Log into the DataParq application.
2. Navigate to **ParQ Your Data** > **Sandbox**.
3. Identify the "Data Lakehouse" card and click the associated **Create New** button.
4. Upload a dynamically provided dataset (passed via CLI arguments).
5. Extract the system-generated **Domain Name** and **Workflow Name** from the upload success modal.
6. Write the Domain Name to a persistent `run_info.json` file for downstream consumption.

**Expected Outcome:**
The file uploads successfully without timeouts, and a valid Domain Name is successfully extracted and saved.

---

### Test Case 2 (TC2): Data Governance Verification
**Objective:** Verify that the dataset uploaded in TC1 correctly propagates to the Data Governance module and is searchable.

**Execution Steps:**
1. Navigate to the **Data Governance** module from the left-hand navigation pane.
2. Retrieve the dynamically generated **Domain Name** from TC1.
3. Locate the global search input in the Governance grid.
4. Search using the extracted Domain Name.
5. Validate that the dataset appears within the search results.

**Expected Outcome:**
The exact Domain Name generated in TC1 is successfully found in the Data Governance search results, confirming data propagation.

---

### Test Case 3 (TC3): Task Execution Status Validation (Data Lakehouse)
**Objective:** Verify that the backend data processing tasks associated with the uploaded file successfully execute and transition to a "Completed" state.

**Execution Steps:**
1. Navigate to the **Monitor** module.
2. Select the **Data Lakehouse** view via the radio button.
3. Locate the "Domain Name" column filter (Kendo Dropdown).
4. Enter the TC1 **Domain Name** to trigger the dropdown overlay, and select the exact domain name from the popup list.
5. Verify the domain is present in the grid results.
6. Navigate to the **Actions** column (Column 11) for that specific row and click the **Task** button (List icon).
7. On the Task Execution page, verify that at least one task row (`k-master-row`) is present in the grid.
8. Monitor the **Status** column badge (`aria-colindex=3`) for all tasks using a long-polling strategy:
   - **Polling Interval:** 30 seconds
   - **Maximum Wait:** 10 minutes

**Validation Rules:**
- **PASS:** Every task successfully transitions from `Hold`/`Queue` to `Completed`.
- **FAIL:** Any task enters a terminal failure state (`Failed`, `Error`, or `Aborted`).
- **FAIL:** The 10-minute timeout is reached before all tasks achieve the `Completed` state.
- **FAIL:** Zero tasks are generated for the workflow.
