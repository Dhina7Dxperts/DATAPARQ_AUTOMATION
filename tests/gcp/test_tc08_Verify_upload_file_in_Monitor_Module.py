import os
import json
import pytest
from utils.logger import get_logger
from pages.monitor_page import MonitorPage
from pages.task_page import TaskPage

logger = get_logger("TC08")

TEST_ID = "TC-08"
STEP_DESCRIPTIONS = {
    1: "Navigate to the Monitor module",
    2: "Select Data Lakehouse Option",
    3: "Search Using Domain Name from TC7",
    4: "Validate Domain Presence in results grid",
    5: "Create a New Batch (Click + icon)",
    6: "Confirm Batch Creation (Click Yes)",
    7: "Search Using Domain Name after batch creation",
    8: "Validate Domain Presence (Exact Match)",
    9: "Open Task (Click the Task button)",
    10: "Identify All Tasks",
    11: "Validate Task Count >= 1",
    12: "Monitor Status Transition to Completed"
}
STEP_EXPECTED = {
    1: "Monitor page loads successfully",
    2: "Data Lakehouse view is selected successfully",
    3: "Search term is entered",
    4: "Domain Name appears in the results grid",
    5: "Confirmation dialog for new batch is displayed",
    6: "Batch creation process begins",
    7: "Search term is entered again",
    8: "Exact matching Domain Name appears in the results grid",
    9: "Task button for exact domain is clicked successfully",
    10: "All task rows are located",
    11: "Task count is greater than or equal to 1",
    12: "All tasks successfully reach Completed status"
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

def test_TC08_verify_upload_file_in_monitor(driver, step_tracker, screenshot_manager):
    logger.info("Starting TC-08 Verify upload file in Monitor Module")
    
    # Check dependencies (TC7 must have passed)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_info_path = os.path.join(base_dir, "run_info.json")

    if not os.path.exists(run_info_path):
        pytest.skip("TC8 BLOCKED: run_info.json not found. TC7 must run first.")

    with open(run_info_path, "r") as f:
        run_info = json.load(f)

    if run_info.get("tc7_status") != "PASS":
        pytest.skip("TC8 BLOCKED: TC7 failed or did not run. Browser session terminated without executing TC8.")

    workflow_name = run_info.get("workflow_name")
    if not workflow_name:
        pytest.skip("TC8 BLOCKED: Domain Name (workflow_name) from TC7 is missing.")

    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    # ── Handle standalone execution (Login if necessary) ──────────────────────
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

    # ── Step 3: Search Using Domain Name from TC7 ──────────────────────────────
    step_tracker["current"] = 3
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Searched for domain '{workflow_name}'.")

    # ── Step 4: Validate Domain Presence ───────────────────────────────────────
    step_tracker["current"] = 4
    monitor_page.validate_domain_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Domain '{workflow_name}' found in results grid.")

    # ── Step 5: Create a New Batch ─────────────────────────────────────────────
    step_tracker["current"] = 5
    monitor_page.click_create_batch(workflow_name)
    _record(step_tracker, screenshot_manager, 5, "Clicked '+' and confirmation dialog appeared.")

    # ── Step 6: Confirm Batch Creation ─────────────────────────────────────────
    step_tracker["current"] = 6
    monitor_page.confirm_batch_creation()
    _record(step_tracker, screenshot_manager, 6, "Clicked 'Yes' to confirm batch creation.")

    # ── Step 7: Search Using Domain Name again ────────────────────────────────
    step_tracker["current"] = 7
    monitor_page.search_domain_via_column_filter(workflow_name)
    _record(step_tracker, screenshot_manager, 7, f"Searched for domain '{workflow_name}' via column filter.")

    # ── Step 8: Validate Domain Presence (Exact Match) ─────────────────────────
    step_tracker["current"] = 8
    monitor_page.validate_domain_presence(workflow_name)
    _record(step_tracker, screenshot_manager, 8, f"Exact match for Domain '{workflow_name}' found in results grid.")

    # ── Step 9: Open Task ─────────────────────────────────────────────────────
    step_tracker["current"] = 9
    monitor_page.click_task_button(workflow_name)
    _record(step_tracker, screenshot_manager, 9, "Task button clicked successfully.")

    # ── Step 10 & 11: Identify Tasks and Validate Count ──────────────────────────
    step_tracker["current"] = 10
    count = task_page.validate_task_count()
    _record(step_tracker, screenshot_manager, 10, f"Successfully identified {count} tasks.")
    
    step_tracker["current"] = 11
    _record(step_tracker, screenshot_manager, 11, f"Task count {count} is >= 1 (PASS).")

    # ── Step 12: Monitor Status Transition ─────────────────────────────────────
    step_tracker["current"] = 12
    # This will poll for up to 30 mins (1800s) and throw an exception if failed or timeout
    task_page.monitor_task_execution(max_wait_seconds=1800, poll_interval=30)
    _record(step_tracker, screenshot_manager, 12, "All tasks successfully changed status to Completed.")

    logger.info("TC08 TEST PASSED ✅")

    # Save tc8 status for subsequent test cases
    run_info["tc8_status"] = "PASS"
    with open(run_info_path, "w") as f:
        json.dump(run_info, f, indent=4)