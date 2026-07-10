import os
import pytest
from datetime import datetime
from selenium import webdriver
from utils.logger import get_logger
from utils.screenshot_manager import ScreenshotManager
from utils.network_capture import NetworkCapture
from utils.report_generator import generate_execution_report, STEP_EXPECTED

logger = get_logger("Conftest")

    # ── Workspace Cleanup ──────────────────────────────────────────────────────────
def pytest_sessionstart(session):
    """
    Hook that runs once before test execution starts.
    Cleans up old execution artifacts, temp files, and logs.
    Recreates necessary reporting directories.
    """
    import shutil
    import glob

    logger.info("Starting workspace cleanup...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, "reports")

    # 1. Delete reports directory if it exists
    if os.path.exists(reports_dir):
        try:
            shutil.rmtree(reports_dir)
            logger.info(f"Deleted directory: {reports_dir}")
        except Exception as e:
            logger.error(f"Failed to delete {reports_dir}: {e}")

    # 2. Delete root-level temp/debug files
    patterns_to_delete = [
        "temp_*", "debug_*", "failed_*", "test_*.html", "test_*.png",
        "page_source.html", "browser_logs.txt", "network_logs.json", "console_logs.txt"
    ]
    
    for pattern in patterns_to_delete:
        matches = glob.glob(os.path.join(base_dir, pattern))
        for file_path in matches:
            if os.path.isfile(file_path):
                # Ensure we don't accidentally delete actual python test files
                if not file_path.endswith(".py"):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

    # 3. Recreate required folder structure
    required_folders = [
        "reports",
        "reports/screenshots",
        "reports/execution_reports", # Assuming DOCX goes here based on existing code
        "reports/documents",         
        "reports/network_logs",
        "reports/html_dumps"
    ]

    for folder in required_folders:
        folder_path = os.path.join(base_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        logger.info(f"Recreated directory: {folder_path}")

    logger.info("Workspace cleanup completed successfully.")

    # Clear any stale run_info.json from previous sessions
    run_info_path = os.path.join(base_dir, "run_info.json")
    if os.path.exists(run_info_path):
        try:
            os.remove(run_info_path)
            logger.info("Cleared stale run_info.json from previous session.")
        except Exception as e:
            logger.warning(f"Could not remove run_info.json: {e}")

# ── Pytest options ─────────────────────────────────────────────────────────────
def pytest_addoption(parser):
    parser.addoption(
        "--upload-file",
        action="store",
        default="test_data/sample.csv",
        help="Path to the file to be uploaded during tests",
    )


# ── Fixtures ───────────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def upload_file_path(request):
    return request.config.getoption("--upload-file")


@pytest.fixture(scope="function")
def step_tracker():
    """Tracks current step number and per-step results for reporting."""
    return {
        "current": 0,
        "results": [],          # list of step result dicts
        "descriptions": {},     # populated by the test script
        "expected": {},         # populated by the test script
        "test_id": "TC",        # test case identifier (e.g., TC-01)
    }


@pytest.fixture(scope="session")
def driver():
    logger.info("Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    # Enable performance/network logging for CDP network capture
    options.add_experimental_option("perfLoggingPrefs", {"enableNetwork": True})
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})

    drv = webdriver.Chrome(options=options)
    yield drv

    logger.info("Test session finished. Closing browser.")
    drv.quit()


@pytest.fixture(scope="function")
def screenshot_manager(driver, request):
    """Creates a ScreenshotManager for the current test function."""
    return ScreenshotManager(driver, request.node.name)


# ── Failure hook ───────────────────────────────────────────────────────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        driver = item.funcargs.get("driver")
        step_tracker = item.funcargs.get("step_tracker", {"current": 0, "results": []})
        sm: ScreenshotManager = item.funcargs.get("screenshot_manager")

        passed = not rep.failed
        failed_step = step_tracker.get("current", 0) if not passed else 0
        error_message = ""
        network_data = None

        step_descriptions = step_tracker.get("descriptions", {})
        step_expected = step_tracker.get("expected", {})
        test_id = step_tracker.get("test_id", "TC")

        if not passed and driver:
            error_message = call.excinfo.exconly() if call.excinfo else "Unknown error"
            logger.error(f"ERROR - Step {failed_step} failed.")

            # Capture failure screenshot
            if sm:
                sm.capture(
                    step_number=failed_step,
                    description=step_descriptions.get(failed_step, "Unknown step"),
                    is_failure=True,
                )
                logger.info("INFO - Failure screenshot captured.")

            # Capture network logs for failed step
            logger.info("INFO - Capturing network request and response.")
            nc = NetworkCapture(driver)
            network_data = nc.capture_network_for_step(
                step_number=failed_step,
                run_dir=sm.get_run_dir() if sm else "reports",
            )

            logger.info("INFO - Saving failure report.")

        # Build step results list
        steps = []
        existing_results = step_tracker.get("results", [])
        existing_step_nums = {r["step"] for r in existing_results}

        for snum in sorted(step_descriptions.keys()):
            if snum in existing_step_nums:
                steps.append(next(r for r in existing_results if r["step"] == snum))
            elif snum < failed_step or (not passed and snum == failed_step):
                # Step was reached but no explicit result logged — infer from failure
                steps.append({
                    "step": snum,
                    "description": step_descriptions.get(snum, ""),
                    "expected": step_expected.get(snum, ""),
                    "actual": "Step failed" if snum == failed_step else "Step completed",
                    "status": "FAIL" if snum == failed_step else "PASS",
                    "error": error_message if snum == failed_step else "",
                })
            else:
                break  # Steps beyond failure point not reached

        # Generate report
        try:
            report_path = generate_execution_report(
                test_name=item.name,
                test_id=test_id,
                passed=passed,
                steps=steps,
                screenshots=sm.get_all() if sm else [],
                run_dir=sm.get_run_dir() if sm else "reports",
                failed_step=failed_step,
                failed_step_description=step_descriptions.get(failed_step, ""),
                error_message=error_message,
                network_data=network_data,
                output_dir="reports/execution_reports",
            )
            logger.info(f"INFO - Execution report saved: {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate execution report: {e}")