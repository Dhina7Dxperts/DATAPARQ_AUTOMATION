import os
import pytest
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.data_lakehouse_page import DataLakehousePage
from pages.file_setup_page import FileSetupPage
from pages.config_page import ConfigPage
from pages.ingest_page import IngestPage
from utils.logger import get_logger
from utils.report_generator import STEP_EXPECTED

logger = get_logger("TC01")

TEST_ID = "TC-01"

STEP_DESCRIPTIONS = {
    1:  "Login to the application and verify Dashboard loads",
    2:  "Navigate to ParQ Your Data and verify Data Lakehouse section is visible",
    3:  "Click Create New inside Data Lakehouse and verify Choose Source page loads",
    4:  "Select Governance tab and verify upload area is visible",
    5:  "Upload the file and verify — fail if app shows an error (e.g. unsupported format like .xlsx)",
    6:  "Verify Next button is enabled after upload and navigate to File Setup page",
    7:  "Validate Metadata tab — verify table and rows are populated",
    8:  "Validate Sample Data tab — verify data rows are populated",
    9:  "Verify Next button is enabled on File Setup page and click it",
    10: "Verify navigation to Config page — Entity Level Setup visible",
    11: "Validate Entity Level Setup section and Source Entities panel are visible",
    12: "Verify Save button is disabled before selecting Data Owners and Data Stewards",
    13: "Select Data Owner (deepanraj.thangaraj@7dxperts.com) and verify selection",
    14: "Select Data Steward (shreyas.senthilkumar@7dxperts.com) and verify selection",
    15: "Verify Save button is enabled after selections and click Save",
    16: "Verify success message 'Config updated successfully' is displayed",
    17: "Verify Next button is enabled after save and click it",
    18: "Verify navigation to Ingest page",
    19: "Select 'Create New' radio button in Add to Data Domain Group",
    20: "Verify Save button is disabled before filling mandatory Ingest fields",
    21: "Enter Domain Name (dynamic: filename without extension)",
    22: "Enter Workflow Name (same as Domain Name)",
    23: "Select Workflow Type: Monthly",
    24: "Enter Expected Runtime (M): 5",
    25: "Enable Notify on Delay checkbox",
    26: "Verify Save button is enabled after all fields filled and click Save",
    27: "Verify save success message: 'Schedule data is saved successfully'",
    28: "Verify Deploy Pipeline button is enabled after save",
    29: "Click Deploy Pipeline button",
    30: "Verify deployment success message is displayed",
}


@pytest.fixture(scope="module", autouse=True)
def setup_test_data(request):
    upload_file_path = request.config.getoption("--upload-file")
    if not os.path.exists(upload_file_path):
        if upload_file_path == "test_data/sample.csv":
            os.makedirs(os.path.dirname(upload_file_path) or ".", exist_ok=True)
            with open(upload_file_path, "w") as f:
                f.write("id,name,SampleValue\n1,MetadataColumn,RowDataValue")
        else:
            pytest.fail(f"FAIL: The provided upload file does not exist: {upload_file_path}")
    yield


def _record(step_tracker, screenshot_manager, step_num: int, actual: str, status: str = "PASS", error: str = ""):
    """Record step result and capture screenshot."""
    step_tracker["results"].append({
        "step": step_num,
        "description": STEP_DESCRIPTIONS.get(step_num, ""),
        "expected": STEP_EXPECTED.get(step_num, ""),
        "actual": actual,
        "status": status,
        "error": error,
    })
    # Capture screenshot for every step EXCEPT login (step 1)
    if step_num > 1 and screenshot_manager:
        screenshot_manager.capture(
            step_number=step_num,
            description=STEP_DESCRIPTIONS.get(step_num, ""),
        )
        logger.info(f"INFO - Screenshot captured for Step {step_num}.")

def test_tc01_governance_file_upload_flow(driver, upload_file_path, step_tracker, screenshot_manager):
    logger.info(f"Starting TC-01 E2E Flow with file: {upload_file_path}")
    
    # Register test metadata in step_tracker for conftest reporting
    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    lakehouse_page = DataLakehousePage(driver)
    file_setup_page = FileSetupPage(driver)
    config_page = ConfigPage(driver)
    ingest_page = IngestPage(driver)

    # ── Step 1: Login ──────────────────────────────────────────────────────────
    step_tracker["current"] = 1
    login_page.navigate()
    login_page.login()
    login_page.wait_for_dashboard()
    # No screenshot for login page
    step_tracker["results"].append({
        "step": 1,
        "description": STEP_DESCRIPTIONS[1],
        "expected": STEP_EXPECTED.get(1, ""),
        "actual": "Login successful — Dashboard loaded",
        "status": "PASS",
        "error": "",
    })
    logger.info("INFO - Step 1 completed. Login successful.")

    # ── Step 2: Navigate to ParQ Your Data ────────────────────────────────────
    step_tracker["current"] = 2
    home_page.open_parq_module()
    home_page.verify_parq_module_loaded()
    _record(step_tracker, screenshot_manager, 2, "ParQ Your Data page loaded — Data Lakehouse and Create New visible")
    logger.info("INFO - Step 2 completed. ParQ Your Data loaded.")

    # ── Step 3: Create New Workflow ───────────────────────────────────────────
    step_tracker["current"] = 3
    lakehouse_page.click_create_new()
    lakehouse_page.wait_for_choose_source_page()
    _record(step_tracker, screenshot_manager, 3, "Choose Source page loaded — all 4 tabs visible")
    logger.info("INFO - Step 3 completed. Choose Source page loaded.")

    # ── Step 4: Select Governance ─────────────────────────────────────────────
    step_tracker["current"] = 4
    lakehouse_page.select_governance()
    lakehouse_page.wait_for_upload_page()
    _record(step_tracker, screenshot_manager, 4, "Governance tab selected — upload area visible")
    logger.info("INFO - Step 4 completed. Governance selected.")

    # ── Step 5: Upload File ───────────────────────────────────────────────────
    step_tracker["current"] = 5
    lakehouse_page.upload_file(upload_file_path)
    file_name = os.path.basename(upload_file_path)
    lakehouse_page.wait_for_upload_complete(file_name)
    _record(step_tracker, screenshot_manager, 5, f"File '{file_name}' uploaded successfully — visible in UI")
    logger.info("INFO - Step 5 completed. CSV upload completed.")

    # ── Step 6: Validate Next button and proceed ──────────────────────────────
    step_tracker["current"] = 6
    lakehouse_page.validate_next_button_and_click()
    file_setup_page.verify_no_error()
    _record(step_tracker, screenshot_manager, 6, "Next button was enabled — navigated to File Setup page without errors")
    logger.info("INFO - Step 6 completed. Next button clicked.")

    # ── Step 7: Metadata Validation ───────────────────────────────────────────
    step_tracker["current"] = 7
    file_setup_page.wait_for_page_load()
    # Set unique entity name to avoid "Entity name already in use" conflicts
    file_setup_page.update_entity_name(upload_file_path)
    file_setup_page.validate_metadata()
    _record(step_tracker, screenshot_manager, 7, "Metadata tab shows populated table with rows")
    logger.info("INFO - Step 7 completed. Metadata validation passed.")

    # ── Step 8: Sample Data Validation ───────────────────────────────────────
    step_tracker["current"] = 8
    file_setup_page.validate_sample_data()
    _record(step_tracker, screenshot_manager, 8, "Sample Data tab shows data rows")
    logger.info("INFO - Step 8 completed. Sample Data validation passed.")

    # ── Step 9: Next button on File Setup page ────────────────────────────────
    step_tracker["current"] = 9
    file_setup_page.verify_next_button_and_click()
    _record(step_tracker, screenshot_manager, 9, "Next button enabled on File Setup page — clicked successfully")
    logger.info("INFO - Step 9 completed. Next button clicked on File Setup page.")

    # ── Step 10: Verify navigation to Config page ────────────────────────────
    step_tracker["current"] = 10
    file_setup_page.assert_final_validation()
    _record(step_tracker, screenshot_manager, 10, "Successfully navigated to Config page")
    logger.info("INFO - Step 10 completed. Navigated to Config page.")

    # ── Step 11: Validate Config page content ─────────────────────────────────
    step_tracker["current"] = 11
    config_page.validate_config_page_loaded()
    _record(step_tracker, screenshot_manager, 11, "Entity Level Setup section and Source Entities panel are visible")
    logger.info("INFO - Step 11 completed. Config page validated.")

    # ── Step 12: Verify Save button disabled before selections ────────────────
    step_tracker["current"] = 12
    config_page.validate_save_button_disabled()
    _record(step_tracker, screenshot_manager, 12, "Save button is disabled before Data Owners and Data Stewards selections")
    logger.info("INFO - Step 12 completed. Save button is disabled (pre-selection).")

    # ── Step 13: Select Data Owner ────────────────────────────────────────────
    step_tracker["current"] = 13
    config_page.select_data_owner("deepanraj.thangaraj@7dxperts.com")
    _record(step_tracker, screenshot_manager, 13, "Data Owner 'deepanraj.thangaraj@7dxperts.com' selected and confirmed")
    logger.info("INFO - Step 13 completed. Data Owner selected.")

    # ── Step 14: Select Data Steward ──────────────────────────────────────────
    step_tracker["current"] = 14
    config_page.select_data_steward("shreyas.senthilkumar@7dxperts.com")
    _record(step_tracker, screenshot_manager, 14, "Data Steward 'shreyas.senthilkumar@7dxperts.com' selected and confirmed")
    logger.info("INFO - Step 14 completed. Data Steward selected.")

    # ── Step 15: Save button enabled & click ──────────────────────────────────
    step_tracker["current"] = 15
    config_page.validate_save_button_enabled_and_click()
    _record(step_tracker, screenshot_manager, 15, "Save button was enabled after selections — clicked successfully")
    logger.info("INFO - Step 15 completed. Save clicked.")

    # ── Step 16: Validate success message ─────────────────────────────────────
    step_tracker["current"] = 16
    config_page.validate_save_success()
    _record(step_tracker, screenshot_manager, 16, "Success message 'Config updated successfully' displayed")
    logger.info("INFO - Step 16 completed. Success message confirmed.")

    # ── Step 17: Next button enabled after save ───────────────────────────────
    step_tracker["current"] = 17
    config_page.validate_next_button_enabled_and_click()
    _record(step_tracker, screenshot_manager, 17, "Next button enabled after Config save — clicked successfully")
    logger.info("INFO - Step 17 completed. Next button clicked on Config page.")

    # ── Step 18: Validate Ingest page ─────────────────────────────────────────
    step_tracker["current"] = 18
    config_page.validate_ingest_page_loaded()
    _record(step_tracker, screenshot_manager, 18, "Successfully navigated to Ingest page")
    logger.info("INFO - Step 18 completed. Ingest page loaded.")

    # ── Step 19: Select Create New radio ─────────────────────────────────────
    step_tracker["current"] = 19
    ingest_page.select_create_new()
    _record(step_tracker, screenshot_manager, 19, "'Create New' radio button selected in Add to Data Domain Group")
    logger.info("INFO - Step 19 completed. Create New selected.")

    # ── Step 20: Verify Save disabled before fields ──────────────────────────
    step_tracker["current"] = 20
    ingest_page.validate_save_disabled()
    _record(step_tracker, screenshot_manager, 20, "Save button is disabled before mandatory fields are filled")
    logger.info("INFO - Step 20 completed. Save is disabled (pre-fill).")

    # ── Step 21: Enter Domain Name ─────────────────────────────────────────
    step_tracker["current"] = 21
    domain_name = ingest_page.enter_domain_name(upload_file_path)
    _record(step_tracker, screenshot_manager, 21, f"Domain Name entered: '{domain_name}'")
    logger.info(f"INFO - Step 21 completed. Domain Name = '{domain_name}'.")

    # ── Step 22: Enter Workflow Name ────────────────────────────────────────
    step_tracker["current"] = 22
    ingest_page.enter_workflow_name(domain_name)
    _record(step_tracker, screenshot_manager, 22, f"Workflow Name entered: '{domain_name}'")
    logger.info(f"INFO - Step 22 completed. Workflow Name = '{domain_name}'.")

    # ── Step 23: Select Workflow Type ───────────────────────────────────────
    step_tracker["current"] = 23
    ingest_page.select_workflow_type("Monthly")
    _record(step_tracker, screenshot_manager, 23, "Workflow Type 'Monthly' selected")
    logger.info("INFO - Step 23 completed. Workflow Type = Monthly.")

    # ── Step 24: Enter Expected Runtime ─────────────────────────────────────
    step_tracker["current"] = 24
    ingest_page.enter_expected_runtime("5")
    _record(step_tracker, screenshot_manager, 24, "Expected Runtime (M) entered: 5")
    logger.info("INFO - Step 24 completed. Expected Runtime = 5.")

    # ── Step 25: Enable Notify on Delay ─────────────────────────────────────
    step_tracker["current"] = 25
    ingest_page.enable_notify_on_delay()
    _record(step_tracker, screenshot_manager, 25, "Notify on Delay checkbox enabled")
    logger.info("INFO - Step 25 completed. Notify on Delay enabled.")

    # ── Step 25b: Update Short Names (prevents "already exists" error)
    ingest_page.update_all_short_names()

    # ── Step 26: Save enabled & click ──────────────────────────────────────────
    step_tracker["current"] = 26
    ingest_page.validate_save_enabled_and_click()
    _record(step_tracker, screenshot_manager, 26, "Save button enabled after all fields filled — clicked")
    logger.info("INFO - Step 26 completed. Save clicked on Ingest page.")

    # ── Step 27: Validate save success message ──────────────────────────────
    step_tracker["current"] = 27
    ingest_page.validate_save_success()
    _record(step_tracker, screenshot_manager, 27, "'Schedule data is saved successfully' message displayed")
    logger.info("INFO - Step 27 completed. Save success confirmed.")

    # ── Step 28: Validate Deploy Pipeline button enabled ──────────────────────
    step_tracker["current"] = 28
    ingest_page.validate_deploy_button_enabled()
    _record(step_tracker, screenshot_manager, 28, "Deploy Pipeline button is enabled after save")
    logger.info("INFO - Step 28 completed. Deploy Pipeline button enabled.")

    # ── Step 29: Click Deploy Pipeline ────────────────────────────────────────
    step_tracker["current"] = 29
    ingest_page.click_deploy_pipeline()
    _record(step_tracker, screenshot_manager, 29, "Deploy Pipeline button clicked")
    logger.info("INFO - Step 29 completed. Deploy Pipeline clicked.")

    # ── Step 30: Validate Deployment Success Message ────────────────────────
    step_tracker["current"] = 30
    ingest_page.validate_deploy_success()
    _record(step_tracker, screenshot_manager, 30, "Deployment success message displayed")
    logger.info("INFO - Step 30 completed. Deployment confirmed.")

    # Save run info for TC2 dependency check
    import json
    abs_upload_path = os.path.abspath(upload_file_path)
    with open("run_info.json", "w") as f:
        json.dump({
            "tc1_status": "PASS",
            "workflow_name": domain_name,
            "file_path": abs_upload_path,
            "file_name": os.path.basename(abs_upload_path),
        }, f, indent=2)
    logger.info(f"TC1 run info saved → workflow: '{domain_name}', file: '{abs_upload_path}'")
    logger.info("TEST PASSED ✅")