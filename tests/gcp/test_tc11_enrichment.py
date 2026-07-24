import pytest
import json
import os
from pages.enrichment_page import EnrichmentPage
from utils.logger import get_logger

logger = get_logger("TC11")

TEST_ID = "TC-11"

STEP_DESCRIPTIONS = {
    1: "Open Enrichment Module - Click the Enrichment module from the left navigation panel.",
    2: "Search Domain - Enter the Domain Name created during TC07 into the search textbox.",
    3: "Select Domain - Click the exact matching Domain displayed in the grid.",
    4: "Select Workflow - In the left-side Workflows panel, click the workflow associated with the domain.",
    5: "Create New Enrichment Entity - Verify + Create New button becomes enabled and click it.",
    6: "Validate Create New Enrichment Entity Dialog - Select the Data Entity created in TC10 (Step 6).",
    7: "Enter Enrichment Entity Name - Enter the name formatted as test_<domain_name>_enrich.",
    8: "Enter Process Name - Enter the same value used in Step 7.",
    9: "Select Data Owner - Open Data Owners dropdown and select shreyas.senthilkumar@7dxperts.com.",
    10: "Enable Historical Data Change Management - Check the checkbox.",
    11: "Continue - Click the Next button and verify navigation.",
    12: "Add First Enrichment Column - Click + Add New Column. Verify dialog is displayed. Enter Column Display Name as sample_1_enrich.",
    13: "Select Data Type - Open the Data Type dropdown and select Integer.",
    14: "Select Column Type - Open the Column Type dropdown and select Free Text.",
    15: "Create Column - Click Add New. Verify that the first enrichment column is created successfully.",
    16: "Add Second Enrichment Column - Click + Add New Column. Verify dialog appears. Enter Column Display Name as sample_2_enrich.",
    17: "Select Data Type - Open the Data Type dropdown and select String.",
    18: "Select Column Type - Open the Column Type dropdown and select Dropdown.",
    19: "Configure Static Dropdown - Select the Static option. Enter 'sample_data' in Dropdown List. Verify it is entered.",
    20: "Create Column - Click Add New. Verify that the second enrichment column is created successfully.",
    21: "Add Third Enrichment Column - Click + Add New Column. Verify dialog appears. Enter Column Display Name as sample_3_enrich.",
    22: "Select Data Type - Open the Data Type dropdown and select String.",
    23: "Select Column Type - Open the Column Type dropdown and select Dropdown.",
    24: "Configure Dynamic Dropdown - Select the Dynamic option. Verify that the Dynamic option is enabled successfully.",
    25: "Create Column - Click Add New. Verify that the third enrichment column is created successfully.",
    26: "Validate All Columns View - Click the All Columns radio button. Verify that the three enrichment columns are displayed.",
    27: "Validate Enrich View - Click the Enrich radio button. Verify that only the enrichment columns are displayed.",
    28: "Save Changes - Click the Save Changes button and verify the success toast.",
    30: "Deploy Pipeline - Click the Deploy Pipeline button and verify successful deployment.",
    31: "Navigate to Monitor - Click the Monitor module from the left navigation menu.",
    32: "Search Using Domain Name - Enter the Domain Name in the Monitor search field.",
    33: "Validate Workflow in Grid - Verify that the Workflow created is displayed in the grid.",
    34: "Open Task Details - Click the Task button for the specific row matching the Domain and Workflow Name.",
    35: "Validate Enrich Layer Tasks - Verify that exactly two Enrich tasks complete successfully."
}

STEP_EXPECTED = {
    1: "Enrichment page opens successfully.",
    2: "Exact matching Domain Name appears in the grid.",
    3: "Domain is selected successfully.",
    4: "Workflow is selected successfully from the left panel.",
    5: "+ Create New button is clicked.",
    6: "Data Entity from TC10 is selected from the dropdown.",
    7: "Enrich Entity Name is entered.",
    8: "Process Name is entered.",
    9: "Data Owner is selected successfully.",
    10: "Historical Data Change Management checkbox is enabled.",
    11: "Next button is clicked and navigates to the next page.",
    12: "Dialog opens and Column Display Name is entered.",
    13: "Data Type Integer is selected successfully.",
    14: "Column Type Free Text is selected successfully.",
    15: "First enrichment column is created successfully.",
    16: "Dialog opens and Column Display Name is entered for second column.",
    17: "Data Type String is selected successfully.",
    18: "Column Type Dropdown is selected successfully.",
    19: "Static option selected and 'sample_data' entered.",
    20: "Second enrichment column is created successfully.",
    21: "Dialog opens and Column Display Name is entered for third column.",
    22: "Data Type String is selected successfully.",
    23: "Column Type Dropdown is selected successfully.",
    24: "Dynamic option selected successfully.",
    25: "Third enrichment column is created successfully.",
    26: "All Columns view selected and the three new enrichment columns are visible.",
    27: "Enrich view selected and only the three new enrichment columns are visible, each appearing exactly once.",
    28: "Save Changes button clicked and success toast appears.",
    30: "Pipeline deployed successfully with 'Your changes have been successfully deployed' toast.",
    31: "Monitor page displayed successfully.",
    32: "Search completed successfully and domain is displayed.",
    33: "Workflow successfully found in the grid.",
    34: "Task Details page opened successfully.",
    35: "Two Enrich tasks found and both reached Completed status."
}

@pytest.fixture(scope="module", autouse=True)
def setup_test_data():
    workflow_name = ""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        run_info_path = os.path.join(base_dir, "run_info.json")
        with open(run_info_path, "r") as f:
            data = json.load(f)
            workflow_name = data.get("workflow_name", "")
            tc10_status = data.get("tc10_status", "")
    except Exception as e:
        logger.error(f"Could not read run_info.json: {e}")
        tc10_status = ""
        
    if not workflow_name:
        pytest.fail("FAIL: Workflow name from TC07 is not available. Run TC07 first.")
    
    yield workflow_name

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

def test_TC11_enrichment_module(driver, step_tracker, screenshot_manager, setup_test_data):
    workflow_name = setup_test_data
    logger.info(f"Starting TC-11 Enrichment Module for workflow: {workflow_name}")

    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    # ── Handle standalone execution (Login if necessary) ──────────────────────
    from pages.login_page import LoginPage
    login_page = LoginPage(driver)
    login_page.login_if_needed()
    logger.info("INFO - Login check completed.")



    enrichment_page = EnrichmentPage(driver)

    # ── Step 1: Open Enrichment Module ──
    step_tracker["current"] = 1
    enrichment_page.click_enrichment_module()
    enrichment_page.verify_enrichment_page_opened()
    _record(step_tracker, screenshot_manager, 1, "Enrichment page is opened successfully")
    logger.info("INFO - Step 1 completed.")

    # ── Step 2: Search Domain ──
    step_tracker["current"] = 2
    enrichment_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 2, f"Exact domain '{workflow_name}' appears in the grid")
    logger.info("INFO - Step 2 completed.")

    # ── Step 3: Select Domain ──
    step_tracker["current"] = 3
    enrichment_page.select_domain_from_grid(workflow_name)
    _record(step_tracker, screenshot_manager, 3, f"Domain '{workflow_name}' was selected from the grid")
    logger.info("INFO - Step 3 completed.")

    # ── Step 4: Select Workflow ──
    step_tracker["current"] = 4
    enrichment_page.select_workflow_from_panel(workflow_name)
    _record(step_tracker, screenshot_manager, 4, f"Selected workflow '{workflow_name}' from the left panel")
    logger.info("INFO - Step 4 completed.")

    # ── Step 5: Create New Enrichment Entity ──
    step_tracker["current"] = 5
    enrichment_page.click_create_new()
    _record(step_tracker, screenshot_manager, 5, "Clicked '+ Create New' button")
    logger.info("INFO - Step 5 completed.")

    # ── Step 6: Validate Create New Enrichment Entity Dialog ──
    step_tracker["current"] = 6
    # TC10 derived entity name format:
    tc10_derived_entity = f"test_{workflow_name}_derive"
    enrichment_page.select_data_entity(tc10_derived_entity)
    _record(step_tracker, screenshot_manager, 6, f"Data Entity '{tc10_derived_entity}' was selected")
    logger.info("INFO - Step 6 completed.")

    # ── Step 7: Enter Enrichment Entity Name ──
    step_tracker["current"] = 7
    enrich_entity_name = f"test_{workflow_name}_enrich"
    enrichment_page.enter_enrich_entity_name(enrich_entity_name)
    _record(step_tracker, screenshot_manager, 7, f"Enrich Entity Name '{enrich_entity_name}' was entered")
    logger.info("INFO - Step 7 completed.")

    # ── Step 8: Enter Process Name ──
    step_tracker["current"] = 8
    enrichment_page.enter_process_name(enrich_entity_name)
    _record(step_tracker, screenshot_manager, 8, f"Process Name '{enrich_entity_name}' was entered")
    logger.info("INFO - Step 8 completed.")

    # ── Step 9: Select Data Owner ──
    step_tracker["current"] = 9
    enrichment_page.select_data_owner("shreyas.senthilkumar@7dxperts.com")
    _record(step_tracker, screenshot_manager, 9, "Data Owner 'shreyas.senthilkumar@7dxperts.com' was selected")
    logger.info("INFO - Step 9 completed.")

    # ── Step 10: Enable Historical Data Change Management ──
    step_tracker["current"] = 10
    enrichment_page.enable_historical_data_change()
    _record(step_tracker, screenshot_manager, 10, "Historical Data Change Management enabled")
    logger.info("INFO - Step 10 completed.")

    # ── Step 11: Continue ──
    step_tracker["current"] = 11
    enrichment_page.click_next()
    _record(step_tracker, screenshot_manager, 11, "Next button clicked")
    logger.info("INFO - Step 11 completed.")

    # ── Step 12: Add First Enrichment Column ──
    step_tracker["current"] = 12
    enrichment_page.click_add_new_column()
    enrichment_page.enter_column_display_name("sample_1_enrich")
    _record(step_tracker, screenshot_manager, 12, "Column Display Name 'sample_1_enrich' entered successfully")
    logger.info("INFO - Step 12 completed.")

    # ── Step 13: Select Data Type ──
    step_tracker["current"] = 13
    enrichment_page.select_data_type("Integer")
    _record(step_tracker, screenshot_manager, 13, "Data Type 'Integer' selected successfully")
    logger.info("INFO - Step 13 completed.")

    # ── Step 14: Select Column Type ──
    step_tracker["current"] = 14
    enrichment_page.select_column_type("Free Text")
    _record(step_tracker, screenshot_manager, 14, "Column Type 'Free Text' selected successfully")
    logger.info("INFO - Step 14 completed.")

    # ── Step 15: Create Column ──
    step_tracker["current"] = 15
    enrichment_page.click_create_enrichment_column()
    _record(step_tracker, screenshot_manager, 15, "First enrichment column created successfully")
    logger.info("INFO - Step 15 completed.")

    # ── Step 16: Add Second Enrichment Column ──
    step_tracker["current"] = 16
    enrichment_page.click_add_new_column()
    enrichment_page.enter_column_display_name("sample_2_enrich")
    _record(step_tracker, screenshot_manager, 16, "Column Display Name 'sample_2_enrich' entered successfully")
    logger.info("INFO - Step 16 completed.")

    # ── Step 17: Select Data Type ──
    step_tracker["current"] = 17
    enrichment_page.select_data_type("String")
    _record(step_tracker, screenshot_manager, 17, "Data Type 'String' selected successfully")
    logger.info("INFO - Step 17 completed.")

    # ── Step 18: Select Column Type ──
    step_tracker["current"] = 18
    enrichment_page.select_column_type("Dropdown")
    _record(step_tracker, screenshot_manager, 18, "Column Type 'Dropdown' selected successfully")
    logger.info("INFO - Step 18 completed.")

    # ── Step 19: Configure Static Dropdown ──
    step_tracker["current"] = 19
    enrichment_page.select_static_dropdown_option()
    enrichment_page.add_static_dropdown_value("sample_data")
    _record(step_tracker, screenshot_manager, 19, "Static dropdown configured with 'sample_data'")
    logger.info("INFO - Step 19 completed.")

    # ── Step 20: Create Column ──
    step_tracker["current"] = 20
    enrichment_page.click_create_enrichment_column()
    _record(step_tracker, screenshot_manager, 20, "Second enrichment column created successfully")
    logger.info("INFO - Step 20 completed.")

    # ── Step 21: Add Third Enrichment Column ──
    step_tracker["current"] = 21
    enrichment_page.click_add_new_column()
    enrichment_page.enter_column_display_name("sample_3_enrich")
    _record(step_tracker, screenshot_manager, 21, "Column Display Name 'sample_3_enrich' entered successfully")
    logger.info("INFO - Step 21 completed.")

    # ── Step 22: Select Data Type ──
    step_tracker["current"] = 22
    enrichment_page.select_data_type("String")
    _record(step_tracker, screenshot_manager, 22, "Data Type 'String' selected successfully")
    logger.info("INFO - Step 22 completed.")

    # ── Step 23: Select Column Type ──
    step_tracker["current"] = 23
    enrichment_page.select_column_type("Dropdown")
    _record(step_tracker, screenshot_manager, 23, "Column Type 'Dropdown' selected successfully")
    logger.info("INFO - Step 23 completed.")

    # ── Step 24: Configure Dynamic Dropdown ──
    step_tracker["current"] = 24
    enrichment_page.select_dynamic_dropdown_option()
    _record(step_tracker, screenshot_manager, 24, "Dynamic option selected successfully")
    logger.info("INFO - Step 24 completed.")

    # ── Step 25: Create Column ──
    step_tracker["current"] = 25
    enrichment_page.click_create_enrichment_column()
    _record(step_tracker, screenshot_manager, 25, "Third enrichment column created successfully")
    logger.info("INFO - Step 25 completed.")

    # ── Step 26: Validate All Columns View ──
    step_tracker["current"] = 26
    enrichment_page.click_all_columns_view()
    expected_enrichment_columns = ["sample_1_enrich", "sample_2_enrich", "sample_3_enrich"]
    enrichment_page.verify_enrichment_columns_in_grid(expected_enrichment_columns)
    _record(step_tracker, screenshot_manager, 26, f"All Columns view selected and columns {expected_enrichment_columns} verified successfully")
    logger.info("INFO - Step 26 completed.")

    # ── Step 27: Validate Enrich View ──
    step_tracker["current"] = 27
    enrichment_page.click_enrich_view()
    enrichment_page.verify_only_enrichment_columns_in_grid(expected_enrichment_columns)
    _record(step_tracker, screenshot_manager, 27, f"Enrich view selected and only columns {expected_enrichment_columns} are present without duplicates")
    logger.info("INFO - Step 27 completed.")

    # ── Step 28: Save Changes ──
    step_tracker["current"] = 28
    enrichment_page.click_save_changes()
    _record(step_tracker, screenshot_manager, 28, "Save Changes button clicked and changes saved successfully")
    logger.info("INFO - Step 28 completed.")

    # ── Step 30: Deploy Pipeline ──
    step_tracker["current"] = 30
    enrichment_page.deploy_pipeline()
    _record(step_tracker, screenshot_manager, 30, "Pipeline deployed successfully verified via exact toast message")
    logger.info("INFO - Step 30 completed.")

    from pages.monitor_page import MonitorPage
    monitor_page = MonitorPage(driver)

    # ── Step 31: Navigate to Monitor ──
    step_tracker["current"] = 31
    monitor_page.navigate_to_monitor()
    _record(step_tracker, screenshot_manager, 31, "Monitor page loaded successfully")
    logger.info("INFO - Step 31 completed.")

    # ── Step 32: Search Using Domain Name ──
    step_tracker["current"] = 32
    monitor_page.search_domain(workflow_name)
    _record(step_tracker, screenshot_manager, 32, f"Domain '{workflow_name}' search completed successfully")
    logger.info("INFO - Step 32 completed.")

    # ── Step 33: Validate Workflow in Grid ──
    step_tracker["current"] = 33
    monitor_page.validate_domain_and_workflow_presence(workflow_name, workflow_name)
    _record(step_tracker, screenshot_manager, 33, f"Exact match for domain '{workflow_name}' and workflow '{workflow_name}' found in grid")
    logger.info("INFO - Step 33 completed.")

    # ── Step 34: Open Task Details ──
    step_tracker["current"] = 34
    monitor_page.click_task_button(workflow_name, workflow_name)
    _record(step_tracker, screenshot_manager, 34, "Task Details page opened successfully")
    logger.info("INFO - Step 34 completed.")

    # ── Step 35: Validate Enrich Layer Tasks ──
    step_tracker["current"] = 35
    monitor_page.validate_multiple_enrich_tasks_status(max_wait=1800, poll_interval=15, screenshot_manager=screenshot_manager, step_num=35)
    _record(step_tracker, screenshot_manager, 35, "Exactly two Enrich tasks were present and completed successfully within 30 minutes")
    logger.info("INFO - Step 35 completed.")

    logger.info("TEST TC11 Enrichment (Steps 1-35) PASSED ✅")
