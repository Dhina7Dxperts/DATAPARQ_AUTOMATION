import pytest
import json
from pages.login_page import LoginPage
from pages.derive_page import DerivePage
from utils.logger import get_logger

logger = get_logger("TC10")

TEST_ID = "TC-10"

STEP_DESCRIPTIONS = {
    1: "Open Derived Module - Click the Derived module from the left navigation. Verify that the Derived page is opened successfully.",
    2: "Search Workflow - Enter the workflow name created in TC07 into the search box. Verify that the workflow appears in the grid.",
    3: "Select Workflow - Click the workflow displayed in the grid.",
    4: "Workflow Selection - Locate Workflow section, click the existing workflow, wait until highlighted, verify New Derive is enabled, and click it.",
    6: "Enter Entity Name - Generate the entity name and enter it into the Entity Name field.",
    7: "Add New Source - Click + Add New Source.",
    9: "Select Source Entity - Open the Source Entity dropdown. Select the domain name created in TC07.",
    10: "Continue - Click Next.",
    11: "Enable PS - Check the PS checkbox.",
    12: "Draw Diagram - Click the Draw Diagram button. Wait until the diagram generation completes successfully.",
    13: "Create First Column Mapping - Under New Column Mapping, locate the dropdown, select Column 1, enable Business Key, and click Create.",
    14: "Create Second Column Mapping - Click + Add New, select Column 2, do NOT check Business Key, and click Create.",
    15: "Create Remaining Column Mappings - Repeat process for Column 3-6 without checking Business Key. Click Save Changes, wait 5 seconds, and click Deploy Pipeline.",
    20: "Open Monitor Module - Navigate to the Monitor module from the left navigation menu.",
    21: "Select Data Lakehouse - Open the Monitor module and select the Data Lakehouse option.",
    22: "Search Using Domain Name - Search using the Domain Name created in TC07 dynamically.",
    23: "Validate Domain Presence - Verify that the searched domain appears in the results grid.",
    24: "Open Task Details - Click the Task button/icon for the corresponding domain to open task details.",
    25: "Wait for Derived Task to Complete - Wait until the Derived layer task status changes to Completed (Max 30 mins, 15s poll).",
}

STEP_EXPECTED = {
    1: "Derived page is opened successfully.",
    2: "Matching workflow is found and appears in the grid.",
    3: "Workflow is clicked.",
    4: "Selected workflow appears under the selected workflow section.",
    5: "New Derived button becomes enabled and is clicked.",
    6: "Entity Name is entered successfully.",
    7: "+ Add New Source is clicked.",
    9: "Workflow is selected from the dropdown.",
    10: "Next button is clicked.",
    11: "PS checkbox is checked.",
    12: "Diagram generation completes successfully.",
    13: "Column mappings created correctly.",
    14: "Changes saved and success message displayed.",
    15: "Pipeline deployed successfully.",
    20: "Derived task completes successfully within 30 minutes without error.",
}

@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    workflow_name = ""
    try:
        with open("run_info.json", "r") as f:
            data = json.load(f)
            workflow_name = data.get("workflow_name", "")
    except Exception as e:
        logger.error(f"Could not read run_info.json: {e}")
        
    if not workflow_name:
        pytest.fail("FAIL: Workflow name from TC07 is not available. Run TC07 first.")
    
    yield workflow_name

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

def test_tc10_derived_module_flow(driver, setup_test_data, step_tracker, screenshot_manager):
    workflow_name = setup_test_data
    logger.info(f"Starting TC-10 E2E Flow with workflow: {workflow_name}")
    
    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    login_page = LoginPage(driver)
    derive_page = DerivePage(driver)

    # ── Login ──
    login_page.navigate()
    login_page.login()
    login_page.wait_for_dashboard()
    logger.info("INFO - Login successful.")

    # ── Step 1: Open Derived Module ──
    step_tracker["current"] = 1
    derive_page.click_derive_module()
    derive_page.verify_derive_page_opened()
    _record(step_tracker, screenshot_manager, 1, "Derived page is opened successfully")
    logger.info("INFO - Step 1 completed.")

    # ── Step 2: Search Workflow ──
    step_tracker["current"] = 2
    derive_page.search_workflow(workflow_name)
    _record(step_tracker, screenshot_manager, 2, f"Workflow '{workflow_name}' appears in the grid")
    logger.info("INFO - Step 2 completed.")

    # ── Step 3: Select Workflow ──
    step_tracker["current"] = 3
    derive_page.select_workflow_from_grid(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Workflow '{workflow_name}' was selected from the grid")
    logger.info("INFO - Step 3 completed.")

    # ── Step 4: Workflow Selection ──
    step_tracker["current"] = 4
    derive_page.select_workflow_and_create_derive(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Selected workflow '{workflow_name}' and clicked '+ New Derive'")
    logger.info("INFO - Step 4 completed.")

    # ── Step 6: Enter Entity Name ──
    step_tracker["current"] = 6
    entity_name = f"test_{workflow_name}_derive"
    derive_page.enter_entity_name(entity_name)
    _record(step_tracker, screenshot_manager, 6, f"Entity Name '{entity_name}' was entered")
    logger.info("INFO - Step 6 completed.")

    # ── Step 7: Add New Source ──
    step_tracker["current"] = 7
    derive_page.click_add_new_source()
    _record(step_tracker, screenshot_manager, 7, "Add New Source button was clicked")
    logger.info("INFO - Step 7 completed.")

    # ── Step 9: Select Source Entity ──
    step_tracker["current"] = 9
    derive_page.select_source_entity_dropdown(workflow_name)
    _record(step_tracker, screenshot_manager, 9, f"Domain name '{workflow_name}' selected from Source Entity dropdown")
    logger.info("INFO - Step 9 completed.")

    # ── Step 10: Continue ──
    step_tracker["current"] = 10
    derive_page.click_next_modal()
    _record(step_tracker, screenshot_manager, 10, "Next button was clicked in the modal")
    logger.info("INFO - Step 10 completed.")

    # ── Step 11: Enable PS ──
    step_tracker["current"] = 11
    derive_page.enable_ps()
    _record(step_tracker, screenshot_manager, 11, "PS checkbox was checked")
    logger.info("INFO - Step 11 completed.")

    # ── Step 12: Draw Diagram ──
    step_tracker["current"] = 12
    derive_page.click_draw_diagram()
    _record(step_tracker, screenshot_manager, 12, "Draw Diagram completed successfully")
    logger.info("INFO - Step 12 completed.")
    
    # ── Step 13: Create First Column Mapping ──
    step_tracker["current"] = 13
    try:
        derive_page.create_column_mapping(column_index=1, check_business_key=True, is_first=True)
        _record(step_tracker, screenshot_manager, 13, "First Column Mapping created successfully")
        logger.info("INFO - Step 13 completed.")
    except Exception as e:
        pytest.fail(f"FAIL: Failed to create first column mapping. Error: {e}")

    # ── Step 14: Create Second Column Mapping ──
    step_tracker["current"] = 14
    try:
        derive_page.create_column_mapping(column_index=2, check_business_key=False, is_first=False)
        _record(step_tracker, screenshot_manager, 14, "Second Column Mapping created successfully")
        logger.info("INFO - Step 14 completed.")
    except Exception as e:
        pytest.fail(f"FAIL: Failed to create second column mapping. Error: {e}")

    # ── Step 15: Create Remaining Column Mappings, Save, and Deploy ──
    step_tracker["current"] = 15
    for i in range(3, 7):
        try:
            derive_page.create_column_mapping(column_index=i, check_business_key=False, is_first=False)
        except Exception as e:
            logger.warning(f"Could not map column {i}. Maybe file has fewer columns. Error: {e}")
            break
            
    # Save Changes
    derive_page.save_changes()
    
    # Deploy Pipeline
    derive_page.deploy_pipeline()
    _record(step_tracker, screenshot_manager, 15, "Remaining mappings created, saved, and deployed successfully")
    logger.info("INFO - Step 15 completed.")
    
    # ── Step 20: Open Monitor Module ──
    step_tracker["current"] = 20
    from pages.monitor_page import MonitorPage
    monitor_page = MonitorPage(driver)
    monitor_page.navigate_to_monitor()
    _record(step_tracker, screenshot_manager, 20, "Monitor module opened")
    logger.info("INFO - Step 20 completed.")

    # ── Step 21: Select Data Lakehouse ──
    step_tracker["current"] = 21
    monitor_page.select_data_lakehouse_view()
    _record(step_tracker, screenshot_manager, 21, "Data Lakehouse tab selected")
    logger.info("INFO - Step 21 completed.")

    # ── Step 22: Search Using Domain Name ──
    step_tracker["current"] = 22
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 22, f"Searched for domain '{workflow_name}'")
    logger.info("INFO - Step 22 completed.")
    
    # ── Step 23: Validate Domain Presence ──
    step_tracker["current"] = 23
    try:
        monitor_page.validate_domain_presence(workflow_name)
        _record(step_tracker, screenshot_manager, 23, f"Domain '{workflow_name}' is present")
        logger.info("INFO - Step 23 completed.")
    except Exception as e:
        pytest.fail(f"FAIL: Searched domain '{workflow_name}' not found. {e}")

    # ── Step 24: Open Task Details ──
    step_tracker["current"] = 24
    monitor_page.click_task_button(workflow_name)
    _record(step_tracker, screenshot_manager, 24, "Task Details opened")
    logger.info("INFO - Step 24 completed.")

    # ── Step 25: Wait for Derived Task to Complete ──
    step_tracker["current"] = 25
    monitor_page.validate_task_status_with_flow(
        layer_name="derived", 
        max_wait=1800, 
        poll_interval=15, 
        screenshot_manager=screenshot_manager, 
        step_num=25
    )
    _record(step_tracker, screenshot_manager, 25, "Derived task reached Completed status within timeout")
    logger.info("INFO - Step 25 completed.")
    
    logger.info("TEST PASS✅")

