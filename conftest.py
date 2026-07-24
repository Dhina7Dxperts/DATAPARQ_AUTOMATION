import os
import pytest
from datetime import datetime
from selenium import webdriver
from utils.logger import get_logger, release_file_handlers, reattach_file_handlers
from utils.screenshot_manager import ScreenshotManager
from selenium.webdriver.common.bidi.network import Network
from utils.report_generator import generate_execution_report, STEP_EXPECTED

# Global list to store failed BiDi network calls for the current test
_current_failed_network_calls = []

def pytest_runtest_setup(item):
    """Clear failed network calls at the start of each test."""
    global _current_failed_network_calls
    _current_failed_network_calls.clear()

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
    import stat

    logger.info("Starting workspace cleanup...")
    import time
    session.config.start_time = time.time()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, "reports")

    def _on_rm_error(func, path, exc_info):
        """
        Error handler for shutil.rmtree.
        On WinError 5 (Access Denied), make the file/folder writable and retry.
        If it still fails (e.g. Chrome has a file lock), log and continue.
        """
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as inner:
            logger.warning(f"Could not remove '{path}' (skipping): {inner}")

    # Backup run_info.json if it exists so we can run isolated tests that depend on it
    run_info_backup = None
    run_info_path = os.path.join(reports_dir, "run_info.json")
    if os.path.exists(run_info_path):
        import json
        with open(run_info_path, "r") as f:
            run_info_backup = json.load(f)

    # 1. Delete reports directory if it exists
    if os.path.exists(reports_dir):
        try:
            # Release log file handles BEFORE deletion so Windows unlocks framework.log
            release_file_handlers()
            shutil.rmtree(reports_dir, onerror=_on_rm_error)
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

    # Re-attach file handlers now that reports/ exists again
    reattach_file_handlers()
    logger.info("Recreated reporting directory structure.")

    if run_info_backup:
        with open(run_info_path, "w") as f:
            import json
            json.dump(run_info_backup, f)
        logger.info("Restored run_info.json from backup.")
        
    logger.info("Workspace cleanup completed successfully.")

    # Clear any stale run_info.json from previous sessions
    run_info_path = os.path.join(base_dir, "run_info.json")
    if os.path.exists(run_info_path):
        try:
            # Commented out so TC2 and TC3 can run independently using previous run_info.json
            # os.remove(run_info_path)
            logger.info("Kept run_info.json for standalone TC execution.")
        except Exception as e:
            logger.warning(f"Could not interact with run_info.json: {e}")

def pytest_addoption(parser):
    parser.addoption(
        "--upload-file",
        action="store",
        default="test_data/sample.csv",
        help="Path to the file to be uploaded during tests",
    )
    parser.addoption(
        "--gcp-file-name",
        action="store",
        default="sample.csv",
        help="File name to retrieve from GCP Bucket"
    )
    parser.addoption(
        "--gcp-flow",
        action="store_true",
        default=False,
        help="Execute the GCP Bucket flow (TC7-TC12)"
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
def driver(request):
    logger.info("Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("detach", True)

    # Enable WebDriver BiDi (Bidirectional API) instead of legacy CDP
    options.enable_bidi = True
        
    # Configure download directory to reports/documents/
    reports_docs_dir = os.path.join(os.getcwd(), "reports", "documents")
    os.makedirs(reports_docs_dir, exist_ok=True)
    prefs = {
        "download.default_directory": reports_docs_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)

    drv = webdriver.Chrome(options=options)
    
    # Setup BiDi Network monitoring for the session
    # network = Network(drv)
    
    # def on_response_completed(response):
    #     """Callback for 'network.responseCompleted' to capture 4xx/5xx errors."""
    #     global _current_failed_network_calls
    #     status = response.response.status
    #     if status >= 400:
    #         url = response.response.url
    #         excluded_extensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff2', '.ico']
    #         if any(url.lower().endswith(ext) for ext in excluded_extensions):
    #             return
    #             
    #         headers_list = response.response.headers
    #         headers_dict = {h['name'].lower(): h['value']['value'] for h in headers_list}
    #         
    #         tracing_tags = {}
    #         for key in ['x-correlation-id', 'x-trace-id', 'traceparent']:
    #             if key in headers_dict:
    #                 tracing_tags[key] = headers_dict[key]
    #                 
    #         try:
    #             body = response.response.body
    #         except AttributeError:
    #             body = "Body fetch not supported or empty"
    #
    #         error_data = {
    #             "request_url": url,
    #             "http_status_code": status,
    #             "status_text": getattr(response.response, 'status_text', ''),
    #             "tracing_tags": tracing_tags,
    #             "all_response_headers": headers_dict,
    #             "response_body": body
    #         }
    #         _current_failed_network_calls.append(error_data)
    #
    # network.add_response_handler(callback=on_response_completed)
        
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

            # Apply Rule 1 Failure Handling: Mark current as FAIL, downstream as BLOCKED
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                run_info_path = os.path.join(base_dir, "run_info.json")
                if os.path.exists(run_info_path):
                    import json, re
                    with open(run_info_path, "r") as f:
                        r_info = json.load(f)
                    match = re.search(r"test_tc0?(\d+)", item.name)
                    if match:
                        tc_num = int(match.group(1))
                        r_info[f"tc{tc_num}_status"] = "FAIL"
                        
                        # Apply block cascade depending on the execution flow (1-6 or 7-12)
                        if tc_num <= 6:
                            block_start, block_end = tc_num + 1, 7
                        else:
                            block_start, block_end = tc_num + 1, 13
                            
                        for i in range(block_start, block_end):
                            r_info[f"tc{i}_status"] = "BLOCKED"
                        with open(run_info_path, "w") as f:
                            json.dump(r_info, f, indent=4)
                        logger.error(f"Execution Rule 1 Triggered: TC{tc_num} FAILED. Marked downstream tests as BLOCKED.")
            except Exception as e:
                logger.error(f"Could not apply block rule to run_info: {e}")

            # Capture failure screenshot (only if the WebDriver session is still alive)
            if sm:
                session_alive = False
                try:
                    _ = driver.window_handles  # lightweight probe
                    session_alive = True
                except Exception:
                    logger.warning("WebDriver session is no longer active — skipping failure screenshot.")

                if session_alive:
                    sm.capture(
                        step_number=failed_step,
                        description=step_descriptions.get(failed_step, "Unknown step"),
                        is_failure=True,
                    )
                    logger.info("INFO - Failure screenshot captured.")

            # --- Extract Failure Evidence to execution_reports/ ---
            safe_test_id = test_id.replace('-', '')
            exec_reports_dir = os.path.join(os.getcwd(), "reports", "execution_reports")
            os.makedirs(exec_reports_dir, exist_ok=True)
            
            import shutil
            # Copy Failure Screenshot
            if sm and sm.get_all():
                last_shot = sm.get_all()[-1]
                if last_shot.get("is_failure"):
                    dest_shot = os.path.join(exec_reports_dir, f"{safe_test_id}_FAILURE_SCREENSHOT.png")
                    shutil.copy2(last_shot["path"], dest_shot)
                    
            # Dump BiDi JSON Request/Response
            global _current_failed_network_calls
            if _current_failed_network_calls:
                json_dest = os.path.join(exec_reports_dir, f"{item.name}_network_failure.json")
                with open(json_dest, "w") as jf:
                    json.dump({
                        "test_name": item.name,
                        "failed_api_calls_count": len(_current_failed_network_calls),
                        "failed_api_calls": _current_failed_network_calls
                    }, jf, indent=4)
                logger.info(f"INFO - Saved BiDi failed network calls to {json_dest}")
                
                # Format a fake network_data dict so docx report generator has something to print
                network_data = {
                    "total_requests": len(_current_failed_network_calls),
                    "total_responses": len(_current_failed_network_calls),
                    "network_summary": [{
                        "url": c["request_url"],
                        "method": "API_CALL",
                        "status": c["http_status_code"],
                        "statusText": c["status_text"],
                        "responseHeaders": c["all_response_headers"]
                    } for c in _current_failed_network_calls]
                }
            # --------------------------------------------------------

            logger.info("INFO - Saving failure report.")

        # Build step results list
        steps = []
        existing_results = step_tracker.get("results", [])
        existing_step_nums = {r["step"] for r in existing_results}

        for snum in sorted(step_descriptions.keys()):
            if snum in existing_step_nums:
                steps.append(next(r for r in existing_results if r["step"] == snum))
            elif not passed and (snum < failed_step or snum == failed_step):
                # Step was reached but no explicit result logged — infer from failure
                steps.append({
                    "step": snum,
                    "description": step_descriptions.get(snum, ""),
                    "expected": step_expected.get(snum, ""),
                    "actual": "Step failed" if snum == failed_step else "Step completed",
                    "status": "FAIL" if snum == failed_step else "PASS",
                    "error": error_message if snum == failed_step else "",
                })
            elif not passed and snum > failed_step:
                break  # Steps beyond failure point were not reached — stop
            # else: test passed but step has no record (merged/skipped step) — skip silently


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

def pytest_sessionfinish(session, exitstatus):
    logger.info("Generating Final Execution Summary Report...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    run_info_path = os.path.join(base_dir, "run_info.json")
    
    if os.path.exists(run_info_path):
        import json, time, glob
        with open(run_info_path, "r") as f:
            r_info = json.load(f)
            
        summary_lines = ["Final Execution Summary Report", "="*30, ""]
        counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "UNKNOWN": 0}
        
        # Determine whether to summarize 1-6 or 7-12 based on what was collected
        # We can check which tests were run in the session
        run_tcs = [item.name for item in session.items if hasattr(item, "name")]
        has_manual = any("tc01" in name or "tc02" in name for name in run_tcs)
        has_gcp = any("tc07" in name or "tc08" in name for name in run_tcs)
        
        tc_range = []
        if has_manual and not has_gcp:
            tc_range = range(1, 7)
        elif has_gcp and not has_manual:
            tc_range = range(7, 13)
        else:
            tc_range = range(1, 13)
            
        for i in tc_range:
            tc_id = f"tc{i}"
            status = r_info.get(f"{tc_id}_status", "BLOCKED") # Default to blocked if missing due to fail-fast
            summary_lines.append(f"TC{i} : {status}")
            counts[status] = counts.get(status, 0) + 1
            
        exec_time = time.time() - getattr(session.config, "start_time", time.time())
        mins, secs = divmod(int(exec_time), 60)
        
        summary_lines.extend([
            "",
            "-"*30,
            f"Total Test Cases: {len(tc_range)}",
            f"Passed Test Cases: {counts.get('PASS', 0)}",
            f"Failed Test Cases: {counts.get('FAIL', 0)}",
            f"Blocked Test Cases: {counts.get('BLOCKED', 0)}",
            f"Total Execution Time: {mins}m {secs}s",
            "",
            "Evidence Document Locations:"
        ])
        
        exec_reports_dir = os.path.join(base_dir, "reports", "execution_reports")
        if os.path.exists(exec_reports_dir):
            docs = glob.glob(os.path.join(exec_reports_dir, "*"))
            for d in sorted(docs):
                summary_lines.append(f"- {d}")
        else:
            summary_lines.append("- No evidence documents found.")
            
        report_path = os.path.join(exec_reports_dir, "Suite_Summary_Report.txt")
        os.makedirs(exec_reports_dir, exist_ok=True)
        with open(report_path, "w") as f:
            f.write("\n".join(summary_lines))
        logger.info(f"Summary Report saved to {report_path}")