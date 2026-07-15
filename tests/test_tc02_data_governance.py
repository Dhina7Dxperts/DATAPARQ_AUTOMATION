import os
import json
import pytest
from pages.data_governance_page import DataGovernancePage
from utils.logger import get_logger

logger = get_logger("TC02")

TEST_ID = "TC-02"

STEP_DESCRIPTIONS = {
    1: "Navigate to Data Governance",
    2: "Open Upload Section",
    3: "Search for Workflow Created in TC1",
    4: "Upload Same File Again",
    5: "Validate Validate Button Behavior",
    6: "Validate Uploaded File",
    7: "Validate Submit Button Behavior",
    8: "Submit File",
    9: "Validate Historical Upload Status",
}

STEP_EXPECTED = {
    1: "Data Governance page loads successfully.",
    2: "Upload page opens successfully.",
    3: "Workflow appears in search results and can be selected.",
    4: "File upload completes successfully.",
    5: "Validate button is disabled initially, then enabled after upload.",
    6: "Success message 'File Validated Successfully' appears.",
    7: "Submit button is disabled initially, then enabled after validation.",
    8: "Success message 'File Submitted Successfully' appears.",
    9: "Historical Upload Status is updated with success state.",
}

def _record(step_tracker, screenshot_manager, step_num: int, actual: str, status: str = "PASS", error: str = ""):
    step_tracker["results"].append({
        "step": step_num,
        "description": STEP_DESCRIPTIONS.get(step_num, ""),
        "expected": STEP_EXPECTED.get(step_num, ""),
        "actual": actual,
        "status": status,
        "error": error,
    })
    if screenshot_manager:
        screenshot_manager.capture(
            step_number=step_num,
            description=STEP_DESCRIPTIONS.get(step_num, ""),
        )
        logger.info(f"INFO - Screenshot captured for Step {step_num}.")


def test_tc02_data_governance_reupload_flow(driver, upload_file_path, step_tracker, screenshot_manager):
    logger.info("Starting TC-02 Data Governance Flow")
    
    # ── Check Prerequisites ───────────────────────────────────────────────────
    if not os.path.exists("run_info.json"):
        pytest.skip(
            "TC2 Skipped: TC1 failed, therefore the required uploaded file is "
            "unavailable for re-upload validation."
        )

    with open("run_info.json", "r") as f:
        run_info = json.load(f)

    if run_info.get("tc1_status") != "PASS":
        pytest.skip("TC2 Skipped: TC1 failed. Browser session terminated without executing TC2.")

    workflow_name = run_info.get("workflow_name")
    if not workflow_name:
        pytest.skip("TC2 Skipped: Workflow name from TC1 is missing.")

    # ── Retrieve TC1 file path — no hardcoding, no manual selection ───────────
    tc1_file_path = run_info.get("file_path")
    tc1_file_name = run_info.get("file_name")
    if not tc1_file_path or not os.path.exists(tc1_file_path):
        pytest.skip(f"TC2 Skipped: TC1 upload file not found at '{tc1_file_path}'.")

    logger.info(f"TC1 Dependency Met. Workflow: '{workflow_name}' | File: '{tc1_file_path}'")
    logger.info(f"Reusing TC1 file → name: '{tc1_file_name}', path: '{tc1_file_path}'")

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
        # We are already in the app (e.g. TC1 ran before this). 
        # Just to be safe, if we somehow landed on the login page, log in.
        from selenium.webdriver.common.by import By
        if driver.find_elements(By.XPATH, "//input[@name='username' or @id='username' or @aria-label='Username']"):
            logger.info("Session active but found login screen. Logging in...")
            login_page.login()

    dg_page = DataGovernancePage(driver)

    # ── Step 1: Navigate to Data Governance ───────────────────────────────────
    step_tracker["current"] = 1
    dg_page.navigate_to_data_governance()
    _record(step_tracker, screenshot_manager, 1, "Data Governance page loaded successfully.")

    # ── Step 2: Open Upload Section ───────────────────────────────────────────
    step_tracker["current"] = 2
    dg_page.open_upload_section()
    _record(step_tracker, screenshot_manager, 2, "Upload section opened.")

    # ── Step 3: Search for Workflow ───────────────────────────────────────────
    step_tracker["current"] = 3
    dg_page.search_workflow(workflow_name)
    dg_page.validate_workflow_exists(workflow_name)
    dg_page.open_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Workflow '{workflow_name}' selected from search.")

    # ── Step 5a: Validate Validate button disabled ─────────────────────────────
    step_tracker["current"] = 5
    dg_page.validate_validate_button_disabled()

    # ── Step 4: Upload Same File Again ─────────────────────────────────────────
    step_tracker["current"] = 4
    dg_page.upload_file(tc1_file_path)
    _record(step_tracker, screenshot_manager, 4, f"File '{tc1_file_name}' re-uploaded (same as TC1).")
    logger.info(f"PASS - Same file reused successfully. File: '{tc1_file_name}'")

    # ── Step 5b: Validate Validate button enabled ──────────────────────────────
    step_tracker["current"] = 5
    dg_page.validate_validate_button()
    _record(step_tracker, screenshot_manager, 5, "Validate button enabled after file upload.")

    # ── Step 7a: Validate Submit button disabled ───────────────────────────────
    step_tracker["current"] = 7
    dg_page.validate_submit_button_disabled()

    # ── Step 6: Validate Uploaded File ─────────────────────────────────────────
    step_tracker["current"] = 6
    dg_page.click_validate()
    _record(step_tracker, screenshot_manager, 6, "File validated successfully.")

    # ── Step 7b: Validate Submit button enabled ────────────────────────────────
    step_tracker["current"] = 7
    dg_page.validate_submit_button()
    _record(step_tracker, screenshot_manager, 7, "Submit button enabled after validation.")

    # ── Step 8: Submit File ────────────────────────────────────────────────────
    step_tracker["current"] = 8
    dg_page.click_submit()
    _record(step_tracker, screenshot_manager, 8, "File submitted successfully.")

    # ── Step 9: Validate Historical Upload Status ──────────────────────────────
    step_tracker["current"] = 9
    dg_page.validate_historical_upload_status()
    _record(step_tracker, screenshot_manager, 9, "Historical Upload Status updated.")

    logger.info("TC02 TEST PASSED ✅")
    
    # Save TC2 status for TC3 dependency
    run_info["tc2_status"] = "PASS"
    with open("run_info.json", "w") as f:
        json.dump(run_info, f, indent=2)
    logger.info("TC2 run info saved.")
