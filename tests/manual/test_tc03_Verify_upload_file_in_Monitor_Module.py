import os
import json
import pytest
from utils.logger import get_logger
from pages.monitor_page import MonitorPage
from pages.task_page import TaskPage

logger = get_logger("TC03")

TEST_ID = "TC-03"
STEP_DESCRIPTIONS = {
    1: "Navigate to the Monitor module",
    2: "Select Data Lakehouse Option",
    3: "Search Using Domain Name from TC1",
    4: "Validate Domain Presence in results grid",
    5: "Click the Task button in the Actions column",
    6: "Identify All Tasks",
    7: "Validate Task Count >= 1",
    8: "Monitor Status Transition to Completed"
}
STEP_EXPECTED = {
    1: "Monitor page loads successfully",
    2: "Data Lakehouse view is selected successfully",
    3: "Search term is entered",
    4: "Domain Name appears in the results grid",
    5: "Task button is clicked successfully",
    6: "All task rows are located",
    7: "Task count is greater than or equal to 1",
    8: "All tasks successfully reach Completed status"
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

def test_tc03_verify_upload_file_in_monitor(driver, step_tracker, screenshot_manager):
    logger.info("Starting TC-03 Verify upload file in Monitor Module")
    
    # Check dependencies (TC1 & TC2 must have passed)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_info_path = os.path.join(base_dir, "run_info.json")

    if not os.path.exists(run_info_path):
        pytest.skip("TC3 BLOCKED: run_info.json not found. TC1 and TC2 must run first.")

    with open(run_info_path, "r") as f:
        run_info = json.load(f)

    if run_info.get("tc2_status") != "PASS":
        pytest.skip("TC3 BLOCKED: TC2 failed or did not run. Browser session terminated without executing TC3.")

    workflow_name = run_info.get("workflow_name")
    if not workflow_name:
        pytest.skip("TC3 BLOCKED: Domain Name (workflow_name) from TC1 is missing.")

    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    # ── Handle standalone/suite execution (login only if not already authenticated) ──
    from pages.login_page import LoginPage
    login_page = LoginPage(driver)
    login_page.login_if_needed()
    logger.info("INFO - Login check completed.")


    monitor_page = MonitorPage(driver)
    task_page = TaskPage(driver)

    # ── Step 1: Open Monitor Module ───────────────────────────────────────────
    step_tracker["current"] = 1
    monitor_page.navigate_to_monitor()
    _record(step_tracker, screenshot_manager, 1, "Monitor page loaded successfully.")

    # ── Step 2: Select Data Lakehouse Option ──────────────────────────────────
    step_tracker["current"] = 2
    monitor_page.select_data_lakehouse_view()
    _record(step_tracker, screenshot_manager, 2, "Data Lakehouse view selected successfully.")

    # ── Step 3: Search Using Domain Name from TC1 ──────────────────────────────
    step_tracker["current"] = 3
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Searched for domain '{workflow_name}'.")

    # ── Step 4: Validate Domain Presence ───────────────────────────────────────
    step_tracker["current"] = 4
    monitor_page.validate_domain_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Domain '{workflow_name}' found in results grid.")

    # ── Step 5: Click Task Button ──────────────────────────────────────────────
    step_tracker["current"] = 5
    monitor_page.click_task_button(workflow_name)
    _record(step_tracker, screenshot_manager, 5, "Task button clicked successfully.")

    # ── Step 6 & 7: Identify Tasks and Validate Count ──────────────────────────
    step_tracker["current"] = 6
    count = task_page.validate_task_count()
    _record(step_tracker, screenshot_manager, 6, f"Successfully identified {count} tasks.")
    
    step_tracker["current"] = 7
    _record(step_tracker, screenshot_manager, 7, f"Task count {count} is >= 1 (PASS).")

    # ── Step 8: Monitor Status Transition ─────────────────────────────────────
    step_tracker["current"] = 8
    # This will poll for up to 30 mins (1800s) and throw an exception if failed or timeout
    task_page.monitor_task_execution(max_wait_seconds=1800, poll_interval=30)
    _record(step_tracker, screenshot_manager, 8, "All tasks successfully changed status to Completed.")

    logger.info("TC03 TEST PASSED ✅")

    # Save tc3 status for tc4
    run_info["tc3_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)