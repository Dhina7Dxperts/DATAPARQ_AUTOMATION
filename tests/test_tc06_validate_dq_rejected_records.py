import pytest
import os
import json
import logging
from pages.data_governance_page import DataGovernancePage
from utils.logger import get_logger
from utils.screenshot_manager import ScreenshotManager

logger = get_logger("TC06")

TEST_ID = "TC06"
STEP_DESCRIPTIONS = {
    1: "Open Data Governance Module",
    2: "Open Upload Section",
    3: "Search Workflow Name",
    4: "Validate Workflow Exists",
    5: "Open Workflow",
    6: "Upload File",
    7: "Click Validate",
    8: "Capture Validation Summary",
    9: "Store Rejected Record Count",
    10: "Validate Downloaded Rejected Records File"
}

STEP_EXPECTED = {
    1: "Data Governance module page loads successfully",
    2: "Upload page is loaded",
    3: "Workflow name entered in search box",
    4: "Workflow found in grid (PASS)",
    5: "Workflow upload page opens successfully",
    6: "File successfully uploaded message is displayed",
    7: "Validation process completes within 30 minutes",
    8: "Valid and Rejected counts are captured from UI",
    9: "Rejected Record Count is stored",
    10: "Downloaded CSV row count exactly matches the UI Rejected Count"
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

def test_tc06_validate_dq_rejected_records(driver, step_tracker, screenshot_manager, upload_file_path):
    logger.info("Starting TC-06 Validate DQ Rejected Records Count")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_info_path = os.path.join(base_dir, "run_info.json")
    
    if not os.path.exists(run_info_path):
        pytest.skip("run_info.json not found. Ensure previous TCs run first.")
        
    with open(run_info_path, "r") as f:
        run_info = json.load(f)
        
    # Test Dependency Rule
    if run_info.get("tc5_status") != "PASS":
        pytest.skip("TC5 did not pass. Skipping TC6 as per preconditions.")
        
    # Dynamic Workflow Name Assignment
    workflow_name = run_info.get("workflow_name")
    
    if not workflow_name:
        pytest.fail("Workflow name is not available in run_info.json. Ensure TC1 and TC2 have run successfully.")
    
    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    from pages.login_page import LoginPage
    login_page = LoginPage(driver)
    if "7dxperts" not in driver.current_url.lower() and "dataparq" not in driver.current_url.lower():
        login_page.navigate()
        login_page.login()
    else:
        from selenium.webdriver.common.by import By
        if driver.find_elements(By.XPATH, "//input[@name='username' or @id='username' or @aria-label='Username']"):
            login_page.login()

    dg_page = DataGovernancePage(driver)

    # Step 1: Open Data Governance Module
    step_tracker["current"] = 1
    dg_page.navigate_to_data_governance()
    _record(step_tracker, screenshot_manager, 1, "Navigated to Data Governance Module.")

    # Step 2: Open Upload Section
    step_tracker["current"] = 2
    dg_page.open_upload_section()
    _record(step_tracker, screenshot_manager, 2, "Opened Upload section.")

    # Step 3: Search Workflow Name
    step_tracker["current"] = 3
    dg_page.search_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Searched for workflow '{workflow_name}'.")

    # Step 4: Validate Workflow Exists
    step_tracker["current"] = 4
    dg_page.validate_workflow_exists(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Workflow '{workflow_name}' found in grid.")

    # Step 5: Open Workflow
    step_tracker["current"] = 5
    dg_page.open_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 5, f"Opened workflow '{workflow_name}'.")

    # Step 6: Upload File
    step_tracker["current"] = 6
    if not upload_file_path:
        pytest.fail("Upload file path not provided.")
    dg_page.upload_file(upload_file_path)
    _record(step_tracker, screenshot_manager, 6, "File successfully uploaded.")

    # Step 7: Click Validate
    step_tracker["current"] = 7
    dg_page.click_validate()
    _record(step_tracker, screenshot_manager, 7, "Validation process completed successfully.")

    # Step 8: Capture Validation Summary
    step_tracker["current"] = 8
    ui_rejected_count = dg_page.get_rejected_records_count()
    _record(step_tracker, screenshot_manager, 8, f"UI Rejected Count captured: {ui_rejected_count}")

    # Step 9: Store Rejected Record Count
    step_tracker["current"] = 9
    logger.info(f"Stored UI Rejected Count = {ui_rejected_count} for comparison.")
    _record(step_tracker, screenshot_manager, 9, f"Stored UI Rejected Count = {ui_rejected_count}")

    # Step 10: Validate Downloaded Rejected Records File
    step_tracker["current"] = 10
    
    import time
    import glob
    import csv
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    download_dir = os.path.join(base_dir, "reports", "documents")
    
    # Record existing files before download
    before_files = set(glob.glob(os.path.join(download_dir, "*")))
    
    dg_page.click_download_rejected()
    
    # Wait for the file to download
    max_wait = 30
    downloaded_file = None
    
    for _ in range(max_wait):
        current_files = set(glob.glob(os.path.join(download_dir, "*")))
        new_files = current_files - before_files
        
        # Check if there's any active download
        active_downloads = glob.glob(os.path.join(download_dir, "*.crdownload"))
        
        if new_files and not active_downloads:
            # Grab the first new file
            downloaded_file = list(new_files)[0]
            time.sleep(1) # Ensure file flush
            break
            
        time.sleep(1)
        
    if not downloaded_file:
        pytest.fail("FAIL: Rejected records CSV file failed to download within 30 seconds.")
        
    logger.info(f"Downloaded file located: {downloaded_file}")
    
    # Count rows
    try:
        with open(downloaded_file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            # Subtract 1 for header
            csv_rejected_count = len(rows) - 1 if rows else 0
    except Exception as e:
        pytest.fail(f"FAIL: Could not read downloaded CSV file. {e}")
        
    logger.info(f"Rejected CSV Rows = {csv_rejected_count}")
    
    if ui_rejected_count == csv_rejected_count:
        _record(step_tracker, screenshot_manager, 10, f"UI Count ({ui_rejected_count}) exactly matches CSV Count ({csv_rejected_count}).")
    else:
        pytest.fail(f"FAIL: UI Rejected Count ({ui_rejected_count}) does NOT match CSV Rejected Count ({csv_rejected_count}).")

    logger.info("TC06 TEST PASSED ✅")
    
    run_info["tc6_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)
