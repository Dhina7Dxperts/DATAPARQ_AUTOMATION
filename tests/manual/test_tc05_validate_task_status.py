import pytest
import os
import json
from pages.monitor_page import MonitorPage
from utils.logger import get_logger

logger = get_logger("TC05")

TEST_ID = "TC05"
STEP_DESCRIPTIONS = {
    1: "Open the Monitor Module",
    2: "Select Data Lakehouse",
    3: "Enter Domain Name",
    4: "Verify Domain Appears in Grid",
    5: "Open Task Details",
    6: "Validate Only Data Quality and Data Lake Layer Status"
}

STEP_EXPECTED = {
    1: "Monitor page loads successfully",
    2: "Data Lakehouse view is loaded",
    3: "Domain name entered in search box",
    4: "Domain exists in grid (PASS)",
    5: "Task details page is loaded successfully",
    6: "dataquality and datalake tasks reach Completed status"
}

def _record(tracker, sm, step_num, actual, status="PASS", error=None):
    sm.capture(step_num, STEP_DESCRIPTIONS[step_num])
    tracker["results"].append({
        "step": step_num,
        "description": STEP_DESCRIPTIONS[step_num],
        "expected": STEP_EXPECTED[step_num],
        "actual": actual,
        "status": status,
        "error": error
    })

def test_tc05_validate_task_status(driver, step_tracker, screenshot_manager):
    logger.info("Starting TC-05 Validate Data Quality and Data Lake Task Completion Status")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_info_path = os.path.join(base_dir, "run_info.json")
    if not os.path.exists(run_info_path):
        pytest.skip("BLOCKED: run_info.json not found. Ensure TC3 runs first.")
        
    with open(run_info_path, "r") as f:
        run_info = json.load(f)
        
    # Test Dependency Rule
    if run_info.get("tc3_status") != "PASS":
        pytest.skip("TC3 did not pass. Blocking TC5 as per preconditions.")
        
    if run_info.get("tc4_status") != "PASS":
        pytest.skip("TC4 did not pass. Blocking TC5 as it requires successful deployment.")
        
    workflow_name = run_info.get("workflow_name")
    if not workflow_name:
        pytest.fail("Workflow name not found in run_info.json")
        
    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    from pages.login_page import LoginPage
    login_page = LoginPage(driver)
    login_page.login_if_needed()
    logger.info("INFO - Login check completed.")


    monitor_page = MonitorPage(driver)

    # Step 1: Open the Monitor Module
    step_tracker["current"] = 1
    monitor_page.navigate_to_monitor()
    _record(step_tracker, screenshot_manager, 1, "Navigated to Monitor Module.")

    # Step 2: Select Data Lakehouse
    step_tracker["current"] = 2
    monitor_page.select_data_lakehouse_view()
    _record(step_tracker, screenshot_manager, 2, "Selected Data Lakehouse view.")

    # Step 3: Enter Domain Name
    step_tracker["current"] = 3
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Entered Domain Name '{workflow_name}'.")

    # Step 4: Verify Domain Appears in Grid
    step_tracker["current"] = 4
    monitor_page.validate_domain_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Domain '{workflow_name}' found in grid.")

    # Step 5: Open Task Details
    step_tracker["current"] = 5
    monitor_page.click_task_button(workflow_name)
    _record(step_tracker, screenshot_manager, 5, "Clicked Task button and opened details.")

    # Step 6: Validate Only Data Quality and Data Lake Layer Status
    step_tracker["current"] = 6
    monitor_page.validate_data_quality_and_lake_status()
    _record(step_tracker, screenshot_manager, 6, "Both dataquality and datalake tasks completed successfully.")

    logger.info("TC05 TEST PASSED ✅")
    
    run_info["tc5_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)
