import os
import json
import pytest
from utils.logger import get_logger
from pages.data_lakehouse_workflow_page import DataLakehouseWorkflowPage

logger = get_logger("TC09")

TEST_ID = "TC-09"
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
    18: "Deploy the Pipeline and Verify Successful Deployment",
    19: "Open the Monitor Module",
    20: "Select Data Lakehouse",
    21: "Enter Domain Name",
    22: "Verify Domain Appears in Grid",
    23: "Open Task Details",
    24: "Validate Only Data Quality and Data Lake Layer Status",
    25: "Validate Record Counts (Staging vs DQ & Lake)"
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
    18: "Pipeline is deployed successfully without timeout",
    19: "Monitor page opens successfully",
    20: "Data Lakehouse page loads successfully",
    21: "Domain Name is entered and search results load",
    22: "Exact Domain Name appears in the grid",
    23: "Task details page for the exact domain is opened",
    24: "Both Data Quality and Data Lake tasks reach Completed status",
    25: "DQ and Data Lake record counts are strictly less than Staging count"
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

def test_TC09_data_lakehouse_workflow(driver, step_tracker, screenshot_manager, upload_file_path, request):
    logger.info("Starting TC-09 Validate Data Lakehouse Workflow Creation")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_info_path = os.path.join(base_dir, "run_info.json")
    if not os.path.exists(run_info_path):
        pytest.skip("run_info.json not found. Ensure TC8 runs first.")
        
    with open(run_info_path, "r") as f:
        run_info = json.load(f)
        
    # if run_info.get("tc8_status") != "PASS":
    #     pytest.skip("TC8 did not pass. Blocking TC09 as per preconditions.")
        
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
    
    # Get the file name from command line or run_info
    gcp_file_name = request.config.getoption("--gcp-file-name")
    if gcp_file_name == "sample.csv" and run_info.get("gcp_file_name"):
        gcp_file_name = run_info.get("gcp_file_name")
        
    from utils.file_reader import get_attribute_value_from_file
    value_to_enter = get_attribute_value_from_file(gcp_file_name, selected_column)
    
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
    
    from utils.file_reader import get_business_key_from_file
    business_key_col = get_business_key_from_file(gcp_file_name)
        
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

    # ── Monitor Validation (Steps 19-24) ──────────────────────────────────────
    from pages.monitor_page import MonitorPage
    monitor_page = MonitorPage(driver)

    # Step 19: Open the Monitor Module
    step_tracker["current"] = 19
    monitor_page.navigate_to_monitor()
    _record(step_tracker, screenshot_manager, 19, "Navigated to Monitor module successfully.")

    # Step 20: Select Data Lakehouse
    step_tracker["current"] = 20
    monitor_page.select_data_lakehouse_view()
    _record(step_tracker, screenshot_manager, 20, "Selected Data Lakehouse view successfully.")

    # Step 21: Enter Domain Name
    step_tracker["current"] = 21
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 21, f"Entered Domain Name '{workflow_name}' and searched.")

    # Step 22: Verify Domain Appears in Grid (Exact Match)
    step_tracker["current"] = 22
    monitor_page.validate_domain_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 22, f"Exact match for Domain '{workflow_name}' found in grid.")

    # Step 23: Open Task Details
    step_tracker["current"] = 23
    monitor_page.click_task_button(workflow_name)
    _record(step_tracker, screenshot_manager, 23, "Task button for exact domain clicked successfully.")

    # Step 24: Validate Only Data Quality and Data Lake Layer Status
    step_tracker["current"] = 24
    target_layers = ["Data Quality", "Data Lake"]
    # Polls every 15s for up to 30 mins, ignoring all other layers, fails on any terminal state
    monitor_page.validate_multiple_layers_status_with_flow(
        target_layers=target_layers,
        max_wait=1800,
        poll_interval=15,
        screenshot_manager=screenshot_manager,
        step_num=24
    )
    _record(step_tracker, screenshot_manager, 24, "Both Data Quality and Data Lake layers successfully reached Completed status.")

    # Step 25: Validate Record Counts
    step_tracker["current"] = 25
    monitor_page.validate_layer_record_counts()
    _record(step_tracker, screenshot_manager, 25, "Record count validation passed (DQ & Lake < Staging).")

    logger.info("TC09 TEST PASSED ✅")
    
    # Save tc9 status
    run_info["tc9_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)
