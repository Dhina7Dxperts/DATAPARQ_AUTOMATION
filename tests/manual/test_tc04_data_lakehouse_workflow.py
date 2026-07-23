import os
import json
import pytest
from utils.logger import get_logger
from pages.data_lakehouse_workflow_page import DataLakehouseWorkflowPage

logger = get_logger("TC04")

TEST_ID = "TC-04"
STEP_DESCRIPTIONS = {
    1: "Navigate to ParQ Your Data",
    2: "Click 'View All' in Data Lakehouse section",
    3: "Search Workflow",
    4: "Validate Workflow Presence",
    5: "Click the Profile Icon for the Selected Flow",
    6: "Click the 'Add / Modify Rules' Button",
    7: "Select DQ Rule as 'Business DQ'",
    8: "Select DQ Action as 'Rejection'",
    9: "Enable Notification",
    10: "Select Attribute",
    11: "Select Comparison Operator",
    12: "Enter Attribute Value",
    13: "Click Create",
    14: "Click the Next Button",
    15: "Select Business Key Column",
    16: "Save the Business Key Configuration",
    17: "Click the Next Button After Saving Business Key",
    18: "Deploy the Pipeline and Verify Successful Deployment"
}

STEP_EXPECTED = {
    1: "Navigate to ParQ Your Data",
    2: "Click 'View All' in Data Lakehouse section",
    3: "Data Lakehouse workflows page is opened",
    4: "Workflow is listed in the grid",
    5: "Flow details page is opened",
    6: "Add / Modify Rules modal opens",
    7: "Business DQ rule option is selected",
    8: "Rejection action is selected",
    9: "Notification is enabled",
    10: "Attribute is selected",
    11: "Comparison operator is selected",
    12: "Attribute value is entered",
    13: "Business DQ rule is created successfully",
    14: "Next button is clicked and Secure page opens",
    15: "Valid Business Key column is selected dynamically",
    16: "Business Key configuration is saved successfully",
    17: "Next button is clicked and the next page loads successfully",
    18: "Pipeline is deployed successfully without timeout"
}

def _record(tracker, sm, step_num, actual, status="PASS", error=None):
    if sm:
        sm.capture(step_number=step_num, description=STEP_DESCRIPTIONS.get(step_num, ""))
    
    tracker["results"].append({
        "step": step_num,
        "description": STEP_DESCRIPTIONS.get(step_num, ""),
        "expected": STEP_EXPECTED.get(step_num, ""),
        "actual": actual,
        "status": status,
        "error": error
    })

def test_tc04_data_lakehouse_workflow(driver, step_tracker, screenshot_manager, upload_file_path):
    logger.info("Starting TC-04 Validate Data Lakehouse Workflow Creation")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_info_path = os.path.join(base_dir, "run_info.json")
    if not os.path.exists(run_info_path):
        pytest.skip("BLOCKED: run_info.json not found. Ensure TC3 runs first.")
        
    with open(run_info_path, "r") as f:
        run_info = json.load(f)
        
    if run_info.get("tc3_status") != "PASS":
        pytest.skip("TC3 did not pass. Blocking TC4 as per preconditions.")
        
    workflow_name = run_info.get("workflow_name")
    if not workflow_name:
        pytest.fail("Workflow name not found in run_info.json")
        
    logger.info(f"Using dynamically generated workflow name: '{workflow_name}'")

    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    # ── Handle standalone execution (Login if necessary) ──────────────────────
    from pages.login_page import LoginPage
    login_page = LoginPage(driver)
    
    # If the current URL is not the app, navigate there
    if "7dxperts" not in driver.current_url.lower() and "dataparq" not in driver.current_url.lower():
        logger.info("Fresh session detected. Navigating to base URL and logging in...")
        login_page.navigate()
        login_page.login()
    else:
        # We are already in the app. Just to be safe, if on login page, log in.
        from selenium.webdriver.common.by import By
        if driver.find_elements(By.XPATH, "//input[@name='username' or @id='username' or @aria-label='Username']"):
            logger.info("Session active but found login screen. Logging in...")
            login_page.login()

    dl_workflow_page = DataLakehouseWorkflowPage(driver)

    # Step 1: Navigate to ParQ Your Data
    step_tracker["current"] = 1
    dl_workflow_page.navigate_to_parq_your_data()
    _record(step_tracker, screenshot_manager, 1, "Navigated to ParQ Your Data successfully.")

    # Step 2: Click 'View All' in Data Lakehouse section
    step_tracker["current"] = 2
    dl_workflow_page.click_view_all_data_lakehouse()
    _record(step_tracker, screenshot_manager, 2, "Clicked View All successfully.")

    # Step 3: Search Workflow
    step_tracker["current"] = 3
    dl_workflow_page.search_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Searched for '{workflow_name}'.")

    # Step 4: Validate Workflow Presence
    step_tracker["current"] = 4
    dl_workflow_page.validate_workflow_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Workflow '{workflow_name}' is present in the grid.")

    # Step 5: Click the Profile Icon for the Selected Flow
    step_tracker["current"] = 5
    dl_workflow_page.click_profile_icon_for_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 5, "Flow details page opened successfully.")

    # Step 6: Click the "Add / Modify Rules" Button
    step_tracker["current"] = 6
    dl_workflow_page.click_add_modify_rules()
    _record(step_tracker, screenshot_manager, 6, "Add/Modify Rules modal opened.")

    # Step 7: Select DQ Rule as "Business DQ"
    step_tracker["current"] = 7
    dl_workflow_page.select_dq_rule("Business DQ")
    _record(step_tracker, screenshot_manager, 7, "Business DQ selected.")

    # Step 8: Select DQ Action as "Rejection"
    step_tracker["current"] = 8
    dl_workflow_page.select_dq_action("Rejection")
    _record(step_tracker, screenshot_manager, 8, "Rejection action selected.")

    # Step 9: Enable Notification
    step_tracker["current"] = 9
    dl_workflow_page.enable_notification()
    _record(step_tracker, screenshot_manager, 9, "Notification enabled.")

    # Step 10: Select Attribute
    step_tracker["current"] = 10
    selected_column = dl_workflow_page.select_first_attribute()
    _record(step_tracker, screenshot_manager, 10, f"Attribute '{selected_column}' selected.")

    # Step 11: Select Comparison Operator
    step_tracker["current"] = 11
    dl_workflow_page.select_operator("=")
    _record(step_tracker, screenshot_manager, 11, "Operator '=' selected.")

    # Step 12: Enter Attribute Value
    step_tracker["current"] = 12
    import csv
    value_to_enter = None
    if os.path.exists(upload_file_path):
        with open(upload_file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Dataparq UI sometimes changes column names to lowercase, so we need case-insensitive matching
            actual_header = None
            if reader.fieldnames:
                for fn in reader.fieldnames:
                    if fn.strip().lower() == selected_column.strip().lower():
                        actual_header = fn
                        break
                        
            if actual_header:
                for row in reader:
                    if actual_header in row and row[actual_header] and str(row[actual_header]).strip() != "":
                        value_to_enter = str(row[actual_header]).strip()
                        break
    if not value_to_enter:
        pytest.fail(f"Could not find any valid non-null value for column '{selected_column}' (or it didn't match CSV headers) in the uploaded file.")
    
    dl_workflow_page.enter_attribute_value(value_to_enter)
    _record(step_tracker, screenshot_manager, 12, f"Value '{value_to_enter}' entered.")

    # Step 13: Click Create
    step_tracker["current"] = 13
    dl_workflow_page.click_create_rule()
    _record(step_tracker, screenshot_manager, 13, "Business DQ rule created.")

    # Step 14: Click the Next Button
    step_tracker["current"] = 14
    dl_workflow_page.click_next_button()
    _record(step_tracker, screenshot_manager, 14, "Next button clicked.")

    # Step 15: Select Business Key Column
    # Important Constraint: Only configure the Business Key column. 
    # Do NOT interact with or modify Mask Column or Contain PII.
    # Exactly one valid Business Key column should be selected.
    step_tracker["current"] = 15
    business_key_col = None
    if os.path.exists(upload_file_path):
        with open(upload_file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers and len(headers) > 0:
                business_key_col = headers[0]

    if not business_key_col:
        pytest.fail("Could not determine the first column from the uploaded file.")
        
    logger.info("Enforcing rule: Interacting strictly with Business Key column only (Mask Column & PII will remain untouched).")
    dl_workflow_page.select_business_key(business_key_col)
    _record(step_tracker, screenshot_manager, 15, f"Exactly one Business Key '{business_key_col}' selected. Mask Column and Contain PII left unchanged.")

    # Step 16: Save the Business Key Configuration
    step_tracker["current"] = 16
    dl_workflow_page.click_save_secure_page()
    _record(step_tracker, screenshot_manager, 16, "Save button clicked on Secure page.")

    # Step 17: Click the Next Button After Saving Business Key
    step_tracker["current"] = 17
    # Wait for the save operation loading indicator/toast to clear before clicking Next
    import time
    time.sleep(3) 
    dl_workflow_page.click_next_button()
    _record(step_tracker, screenshot_manager, 17, "Next button clicked after saving Business Key.")

    # Step 18: Deploy the Pipeline and Verify Successful Deployment
    step_tracker["current"] = 18
    dl_workflow_page.deploy_pipeline()
    _record(step_tracker, screenshot_manager, 18, "Pipeline successfully deployed after waiting.")

    logger.info("TC04 TEST PASSED ✅")
    
    # Save tc4 status
    run_info["tc4_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)
