import json
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("NetworkCapture")


class NetworkCapture:
    """
    Captures browser network logs using Chrome DevTools Protocol (CDP).
    Requires Chrome launched with performance logging enabled.
    """

    def __init__(self, driver):
        self.driver = driver

    def _get_performance_logs(self) -> list[dict]:
        try:
            return self.driver.get_log("performance")
        except Exception as e:
            logger.warning(f"Could not retrieve performance logs: {e}")
            return []

    def capture_network_for_step(self, step_number: int, run_dir: str) -> dict:
        """
        Reads Chrome performance logs, filters for Network.responseReceived events,
        and saves request/response JSON files for the failed step.

        Returns a dict with summary info for embedding in the report.
        """
        logs = self._get_performance_logs()
        requests = []
        responses = []
        network_summary = []

        for entry in logs:
            try:
                msg = json.loads(entry.get("message", "{}")).get("message", {})
                method = msg.get("method", "")
                params = msg.get("params", {})

                if method == "Network.requestWillBeSent":
                    req = params.get("request", {})
                    requests.append({
                        "requestId": params.get("requestId", ""),
                        "url": req.get("url", ""),
                        "method": req.get("method", ""),
                        "headers": req.get("headers", {}),
                        "postData": req.get("postData", ""),
                        "timestamp": params.get("timestamp", ""),
                    })

                elif method == "Network.responseReceived":
                    resp = params.get("response", {})
                    responses.append({
                        "requestId": params.get("requestId", ""),
                        "url": resp.get("url", ""),
                        "status": resp.get("status", ""),
                        "statusText": resp.get("statusText", ""),
                        "headers": resp.get("headers", {}),
                        "mimeType": resp.get("mimeType", ""),
                        "timing": resp.get("timing", {}),
                    })

            except Exception:
                continue

        # Match requests with responses
        req_map = {r["requestId"]: r for r in requests}
        for resp in responses:
            rid = resp["requestId"]
            matched_req = req_map.get(rid, {})
            timing = resp.get("timing", {})
            response_time_ms = ""
            if timing and timing.get("sendStart") is not None and timing.get("receiveHeadersEnd") is not None:
                response_time_ms = f"{timing['receiveHeadersEnd'] - timing['sendStart']:.2f} ms"

            entry_summary = {
                "url": resp.get("url", "N/A"),
                "method": matched_req.get("method", "N/A"),
                "status": resp.get("status", "N/A"),
                "statusText": resp.get("statusText", "N/A"),
                "requestHeaders": matched_req.get("headers", {}),
                "requestPayload": matched_req.get("postData", ""),
                "responseHeaders": resp.get("headers", {}),
                "responseTime": response_time_ms,
            }
            network_summary.append(entry_summary)

        # Save JSON files — ensure the directory exists first
        os.makedirs(run_dir, exist_ok=True)
        req_path = os.path.join(run_dir, f"Step_{step_number:02d}_Request.json")
        resp_path = os.path.join(run_dir, f"Step_{step_number:02d}_Response.json")

        with open(req_path, "w", encoding="utf-8") as f:
            json.dump(requests, f, indent=2)
        with open(resp_path, "w", encoding="utf-8") as f:
            json.dump(responses, f, indent=2)

        logger.info(f"INFO - Network logs saved: {os.path.basename(req_path)}, {os.path.basename(resp_path)}")

        return {
            "network_summary": network_summary,
            "request_file": req_path,
            "response_file": resp_path,
            "total_requests": len(requests),
            "total_responses": len(responses),
        }
