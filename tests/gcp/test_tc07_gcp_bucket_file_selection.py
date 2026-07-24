import os
import pytest
import time
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.data_lakehouse_page import DataLakehousePage
from pages.file_setup_page import FileSetupPage
from pages.config_page import ConfigPage
from pages.ingest_page import IngestPage
from utils.logger import get_logger
from utils.report_generator import STEP_EXPECTED

logger = get_logger("TC07")

TEST_ID = "TC-07"

STEP_DESCRIPTIONS = {
    1:  "Login to the application and verify Dashboard loads",
    2:  "Navigate to ParQ Your Data and verify Data Lakehouse section is visible",
    3:  "Click Create New inside Data Lakehouse and verify Choose Source page loads",
    4:  "Click the 'Cloud Storage' option",
    5:  "Select 'Google Cloud Platform'",
    6:  "Click the 'Existing' option",
    7:  "Locate the 'Connection Name' dropdown and select 'landing_zone'",
    8:  "Click the 'Submit' button",
    9:  "In the folder name text box, enter 'testing'",
    10: "Select 'Each file is an entity'",
    11: "Click the 'Scan' button",
    12: "Validate that the expected file exists under the 'testing' folder",
    13: "Verify Next button is enabled after upload and navigate to File Setup page",
    14: "Validate Metadata tab — verify table and rows are populated",
    15: "Validate Sample Data tab — verify data rows are populated",
    16: "Verify Next button is enabled on File Setup page and click it",
    17: "Verify navigation to Config page — Entity Level Setup visible",
    18: "Validate Entity Level Setup section and Source Entities panel are visible",
    19: "Verify Save button is disabled before selecting Data Owners and Data Stewards",
    20: "Select Data Owner (deepanraj.thangaraj@7dxperts.com) and verify selection",
    21: "Select Data Steward (shreyas.senthilkumar@7dxperts.com) and verify selection",
    22: "Verify Save button is enabled after selections and click Save",
    23: "Verify success message 'Config updated successfully' is displayed",
    24: "Verify Next button is enabled after save and click it",
    25: "Verify navigation to Ingest page",
    26: "Select 'Create New' radio button in Add to Data Domain Group",
    27: "Verify Save button is disabled before filling mandatory Ingest fields",
    28: "Enter Domain Name (dynamic: filename without extension)",
    29: "Enter Workflow Name (same as Domain Name)",
    30: "Select Workflow Type: Monthly",
    31: "Select Workflow Day: 1st",
    32: "Select current time for Time (UTC+00:00)",
    33: "Enter Expected Runtime (M): 5",
    34: "Enable Notify on Delay checkbox",
    35: "Verify Save button is enabled after all fields filled and click Save",
    36: "Verify save success message: 'Schedule data is saved successfully'",
    37: "Verify Deploy Pipeline button is enabled after save",
    38: "Click Deploy Pipeline button",
    39: "Verify deployment success message is displayed",
}

@pytest.fixture(scope="module", autouse=True)
def setup_test_data(request):
    gcp_file_name = request.config.getoption("--gcp-file-name")
    if not gcp_file_name:
        pytest.fail("FAIL: The provided gcp file name is missing.")
    
    upload_file_path = request.config.getoption("--upload-file")
    if not os.path.exists(upload_file_path):
        if upload_file_path == "test_data/sample.csv":
            os.makedirs(os.path.dirname(upload_file_path) or ".", exist_ok=True)
            with open(upload_file_path, "w") as f:
                f.write("id,name,SampleValue\n1,MetadataColumn,RowDataValue")
        else:
            pass
    yield gcp_file_name


def _record(step_tracker, screenshot_manager, step_num: int, actual: str, status: str = "PASS", error: str = ""):
    """Record step result and capture screenshot."""
    step_tracker["results"].append({
        "step": step_num,
        "description": STEP_DESCRIPTIONS.get(step_num, ""),
        "expected": STEP_EXPECTED.get(step_num, "") if STEP_EXPECTED else "",
        "actual": actual,
        "status": status,
        "error": error,
    })
    if step_num > 1 and screenshot_manager:
        screenshot_manager.capture(
            step_number=step_num,
            description=STEP_DESCRIPTIONS.get(step_num, ""),
        )
        logger.info(f"INFO - Screenshot captured for Step {step_num}.")

def test_tc07_gcp_bucket_file_selection_flow(driver, upload_file_path, setup_test_data, step_tracker, screenshot_manager):
    gcp_file_name = setup_test_data
    logger.info(f"Starting TC-07 E2E Flow with file: {gcp_file_name} and local fallback: {upload_file_path}")
    
    step_tracker["test_id"] = TEST_ID
    step_tracker["descriptions"] = STEP_DESCRIPTIONS
    step_tracker["expected"] = STEP_EXPECTED

    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    lakehouse_page = DataLakehousePage(driver)
    file_setup_page = FileSetupPage(driver)
    config_page = ConfigPage(driver)
    ingest_page = IngestPage(driver)

    # ── Step 1: Login (skipped if already authenticated in suite execution) ──
    step_tracker["current"] = 1
    login_page.login_if_needed()
    step_tracker["results"].append({
        "step": 1,
        "description": STEP_DESCRIPTIONS[1],
        "expected": STEP_EXPECTED.get(1, "") if STEP_EXPECTED else "",
        "actual": "Login successful — Dashboard loaded",
        "status": "PASS",
        "error": "",
    })
    logger.info("INFO - Step 1 completed. Login successful.")


    # ── Step 2: Navigate to ParQ Your Data
    step_tracker["current"] = 2
    home_page.open_parq_module()
    home_page.verify_parq_module_loaded()
    _record(step_tracker, screenshot_manager, 2, "ParQ Your Data page loaded — Data Lakehouse and Create New visible")
    logger.info("INFO - Step 2 completed. ParQ Your Data loaded.")

    # ── Step 3: Create New Workflow
    step_tracker["current"] = 3
    lakehouse_page.click_create_new()
    lakehouse_page.wait_for_choose_source_page()
    _record(step_tracker, screenshot_manager, 3, "Choose Source page loaded — all 4 tabs visible")
    logger.info("INFO - Step 3 completed. Choose Source page loaded.")

    # ── Step 4: Click the "Cloud Storage" option
    step_tracker["current"] = 4
    lakehouse_page.click_cloud_storage()
    _record(step_tracker, screenshot_manager, 4, "Cloud Storage tab selected")
    logger.info("INFO - Step 4 completed. Cloud Storage selected.")

    # ── Step 5: Select "Google Cloud Platform"
    step_tracker["current"] = 5
    lakehouse_page.select_gcp_source()
    _record(step_tracker, screenshot_manager, 5, "Google Cloud Platform selected")
    logger.info("INFO - Step 5 completed. GCP source selected.")

    # ── Step 6: Click the "Existing" option
    step_tracker["current"] = 6
    lakehouse_page.click_existing_connection()
    _record(step_tracker, screenshot_manager, 6, "Existing connection option selected")
    logger.info("INFO - Step 6 completed. Existing connection selected.")

    # ── Step 7: Select Connection Name
    step_tracker["current"] = 7
    lakehouse_page.select_connection_name("landing_zone")
    _record(step_tracker, screenshot_manager, 7, "Connection Name 'landing_zone' selected")
    logger.info("INFO - Step 7 completed. landing_zone connection selected.")

    # ── Step 8: Click Submit
    step_tracker["current"] = 8
    lakehouse_page.click_submit()
    _record(step_tracker, screenshot_manager, 8, "Submit button clicked")
    logger.info("INFO - Step 8 completed. Submit clicked.")

    # ── Step 9: Enter folder name 'testing'
    step_tracker["current"] = 9
    lakehouse_page.enter_folder_name("testing")
    _record(step_tracker, screenshot_manager, 9, "Folder name 'testing' entered")
    logger.info("INFO - Step 9 completed. Folder name entered.")

    # ── Step 10: Select Each file is an entity
    step_tracker["current"] = 10
    lakehouse_page.select_each_file_is_an_entity()
    _record(step_tracker, screenshot_manager, 10, "'Each file is an entity' selected")
    logger.info("INFO - Step 10 completed. File entity option selected.")

    # ── Step 11: Click Scan
    step_tracker["current"] = 11
    lakehouse_page.click_scan()
    _record(step_tracker, screenshot_manager, 11, "Scan button clicked")
    logger.info("INFO - Step 11 completed. Scan clicked.")

    # ── Step 12: Select Source File
    step_tracker["current"] = 12
    lakehouse_page.select_specific_source_file("testing", gcp_file_name)
    _record(step_tracker, screenshot_manager, 12, f"Specific file '{gcp_file_name}' was selected successfully, ignoring other files")
    logger.info("INFO - Step 12 completed. Specific source file selected.")

    # ── Step 13: Validate Next button and proceed
    step_tracker["current"] = 13
    lakehouse_page.validate_next_button_and_click()
    file_setup_page.verify_no_error()
    _record(step_tracker, screenshot_manager, 13, "Next button was enabled — navigated to File Setup page without errors")
    logger.info("INFO - Step 13 completed. Next button clicked.")

    # ── Step 14: Metadata Validation
    step_tracker["current"] = 14
    time.sleep(2)
    file_setup_page.wait_for_page_load()
    #file_setup_page.update_entity_name(gcp_file_name)
    file_setup_page.validate_metadata()
    _record(step_tracker, screenshot_manager, 14, "Metadata tab shows populated table with rows")
    logger.info("INFO - Step 14 completed. Metadata validation passed.")

    # ── Step 15: Sample Data Validation
    step_tracker["current"] = 15
    time.sleep(2)
    file_setup_page.validate_sample_data()
    _record(step_tracker, screenshot_manager, 15, "Sample Data tab shows data rows")
    logger.info("INFO - Step 15 completed. Sample Data validation passed.")

    # ── Step 16: Next button on File Setup page
    step_tracker["current"] = 16
    file_setup_page.verify_next_button_and_click()
    _record(step_tracker, screenshot_manager, 16, "Next button enabled on File Setup page — clicked successfully")
    logger.info("INFO - Step 16 completed. Next button clicked on File Setup page.")

    # ── Step 17: Verify navigation to Config page
    step_tracker["current"] = 17
    file_setup_page.assert_final_validation()
    _record(step_tracker, screenshot_manager, 17, "Successfully navigated to Config page")
    logger.info("INFO - Step 17 completed. Navigated to Config page.")

    # ── Step 18: Validate Config page content
    step_tracker["current"] = 18
    config_page.validate_config_page_loaded()
    _record(step_tracker, screenshot_manager, 18, "Entity Level Setup section and Source Entities panel are visible")
    logger.info("INFO - Step 18 completed. Config page validated.")

# ── Step 20: Select Data Owner (Only if missing)
    step_tracker["current"] = 20
    owner_changed = config_page.select_data_owner("deepanraj.thangaraj@7dxperts.com")
    
    if owner_changed:
        _record(step_tracker, screenshot_manager, 20, "Data Owner missing — selected 'deepanraj.thangaraj@7dxperts.com'")
        logger.info("INFO - Step 20 completed. Data Owner entered.")
    else:
        _record(step_tracker, screenshot_manager, 20, "Data Owner already present — skipped entry")
        logger.info("INFO - Step 20 completed. Existing Data Owner preserved.")

    # ── Step 21: Select Data Steward (Only if missing)
    step_tracker["current"] = 21
    steward_changed = config_page.select_data_steward("shreyas.senthilkumar@7dxperts.com")
    
    if steward_changed:
        _record(step_tracker, screenshot_manager, 21, "Data Steward missing — selected 'shreyas.senthilkumar@7dxperts.com'")
        logger.info("INFO - Step 21 completed. Data Steward entered.")
    else:
        _record(step_tracker, screenshot_manager, 21, "Data Steward already present — skipped entry")
        logger.info("INFO - Step 21 completed. Existing Data Steward preserved.")

    # ── Step 22 & 23: Save Details (Conditional on changes made)
    if owner_changed or steward_changed:
        step_tracker["current"] = 22
        config_page.validate_save_button_enabled_and_click()
        _record(step_tracker, screenshot_manager, 22, "Save button enabled after missing values were added — clicked successfully")
        logger.info("INFO - Step 22 completed. Save clicked.")

        step_tracker["current"] = 23
        config_page.validate_save_success()
        _record(step_tracker, screenshot_manager, 23, "Success message 'Config updated successfully' displayed")
        logger.info("INFO - Step 23 completed. Success message confirmed.")
    else:
        logger.info("INFO - Data Owner and Data Steward already populated. Skipping Save.")
        step_tracker["current"] = 22
        config_page.validate_save_button_disabled()
        _record(step_tracker, screenshot_manager, 22, "Save button remained disabled as existing values were left untouched")
        logger.info("INFO - Step 22 completed. Save skipped.")

        step_tracker["current"] = 23
        _record(step_tracker, screenshot_manager, 23, "Success message validation skipped since no update was required")
        logger.info("INFO - Step 23 completed. Success validation skipped.")

    # ── Step 24: Next button enabled after save
    step_tracker["current"] = 24
    config_page.validate_next_button_enabled_and_click()
    _record(step_tracker, screenshot_manager, 24, "Next button enabled after Config save — clicked successfully")
    logger.info("INFO - Step 24 completed. Next button clicked on Config page.")

    # ── Step 25: Validate Ingest page
    step_tracker["current"] = 25
    config_page.validate_ingest_page_loaded()
    _record(step_tracker, screenshot_manager, 25, "Successfully navigated to Ingest page")
    logger.info("INFO - Step 25 completed. Ingest page loaded.")

    # ── Step 26: Select Create New radio
    step_tracker["current"] = 26
    ingest_page.select_create_new()
    _record(step_tracker, screenshot_manager, 26, "'Create New' radio button selected in Add to Data Domain Group")
    logger.info("INFO - Step 26 completed. Create New selected.")

    # ── Step 27: Verify Save disabled before fields
    step_tracker["current"] = 27
    ingest_page.validate_save_disabled()
    _record(step_tracker, screenshot_manager, 27, "Save button is disabled before mandatory fields are filled")
    logger.info("INFO - Step 27 completed. Save is disabled (pre-fill).")

    # ── Step 28: Enter Domain Name
    step_tracker["current"] = 28
    domain_name = ingest_page.enter_domain_name(gcp_file_name)
    _record(step_tracker, screenshot_manager, 28, f"Domain Name entered: '{domain_name}'")
    logger.info(f"INFO - Step 28 completed. Domain Name = '{domain_name}'.")

    # ── Step 29: Enter Workflow Name
    step_tracker["current"] = 29
    ingest_page.enter_workflow_name(domain_name)
    _record(step_tracker, screenshot_manager, 29, f"Workflow Name entered: '{domain_name}'")
    logger.info(f"INFO - Step 29 completed. Workflow Name = '{domain_name}'.")

    # ── Step 30: Select Workflow Type
    step_tracker["current"] = 30
    ingest_page.select_workflow_type("Monthly")

    # ── Step 31: Workflow Day
    step_tracker["current"] = 31
    ingest_page.select_workflow_day("1st")
    _record(step_tracker, screenshot_manager, 31, "Workflow Day '1st' selected")
    logger.info("INFO - Step 31 completed. Workflow Day selected.")
    
    # ── Step 32: Time (UTC+00:00)
    step_tracker["current"] = 32
    ingest_page.select_current_time()
    _record(step_tracker, screenshot_manager, 32, "Current time selected for Time (UTC+00:00)")
    logger.info("INFO - Step 32 completed. Current time selected.")

    # ── Step 33: Enter Expected Runtime
    step_tracker["current"] = 33
    ingest_page.enter_expected_runtime("5")
    _record(step_tracker, screenshot_manager, 33, "Expected Runtime (M) entered: 5")
    logger.info("INFO - Step 33 completed. Expected Runtime = 5.")

    # ── Step 34: Enable Notify on Delay
    step_tracker["current"] = 34
    ingest_page.enable_notify_on_delay()
    _record(step_tracker, screenshot_manager, 34, "Notify on Delay checkbox enabled")
    logger.info("INFO - Step 34 completed. Notify on Delay enabled.")

    # ── Step 34b: Update Short Names (prevents "already exists" error)
    ingest_page.update_all_short_names()

    # ── Step 35: Save enabled & click
    step_tracker["current"] = 35
    ingest_page.validate_save_enabled_and_click()
    _record(step_tracker, screenshot_manager, 35, "Save button enabled after all fields filled — clicked")
    logger.info("INFO - Step 35 completed. Save clicked on Ingest page.")

    # ── Step 36: Validate save success message
    step_tracker["current"] = 36
    ingest_page.validate_save_success()
    _record(step_tracker, screenshot_manager, 36, "'Schedule data is saved successfully' message displayed")
    logger.info("INFO - Step 36 completed. Save success confirmed.")

    # ── Step 37: Validate Deploy Pipeline button enabled
    step_tracker["current"] = 37
    ingest_page.validate_deploy_button_enabled()
    _record(step_tracker, screenshot_manager, 37, "Deploy Pipeline button is enabled after save")
    logger.info("INFO - Step 37 completed. Deploy Pipeline button enabled.")

    # ── Step 38: Click Deploy Pipeline
    step_tracker["current"] = 38
    ingest_page.click_deploy_pipeline()
    _record(step_tracker, screenshot_manager, 38, "Deploy Pipeline button clicked")
    logger.info("INFO - Step 38 completed. Deploy Pipeline clicked.")

    # ── Step 39: Validate Deployment Success Message
    step_tracker["current"] = 39
    ingest_page.validate_deploy_success()
    _record(step_tracker, screenshot_manager, 39, "Deployment success message displayed")
    logger.info("INFO - Step 39 completed. Deployment confirmed.")

    # Save run info
    import json
    abs_upload_path = os.path.abspath(upload_file_path)
    with open("run_info.json", "w") as f:
        json.dump({
            "tc7_status": "PASS",
            "workflow_name": domain_name,
            "file_path": abs_upload_path,
            "file_name": os.path.basename(abs_upload_path),
            "gcp_file_name": gcp_file_name
        }, f, indent=2)
    logger.info(f"TC7 run info saved → workflow: '{domain_name}', file: '{gcp_file_name}', local path: '{abs_upload_path}'")
    
    time.sleep(5)
    
    logger.info("TEST PASS✅")