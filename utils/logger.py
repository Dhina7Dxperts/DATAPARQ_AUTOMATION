import logging
import os


LOG_FILE = os.path.join("reports", "framework.log")


def get_logger(name):
    logger = logging.getLogger(name)

    # Prevent duplicate handlers if the logger is called multiple times
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

        # 1. Console Handler (Streams logs live to terminal window)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # 2. File Handler (Appends logs permanently to reports/framework.log)
        os.makedirs("reports", exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def release_file_handlers():
    """
    Flush and close all FileHandler instances across every active logger.
    Call this before deleting the reports directory so Windows releases
    the lock on reports/framework.log (WinError 32).
    After the directory is recreated, the next call to get_logger() will
    re-attach a fresh FileHandler automatically.
    """
    for name, lgr in list(logging.Logger.manager.loggerDict.items()):
        if not isinstance(lgr, logging.Logger):
            continue
        for handler in list(lgr.handlers):
            if isinstance(handler, logging.FileHandler):
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
                lgr.removeHandler(handler)


def reattach_file_handlers():
    """
    Re-create FileHandlers for every active logger after the reports
    directory has been recreated.
    """
    os.makedirs("reports", exist_ok=True)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    for name, lgr in list(logging.Logger.manager.loggerDict.items()):
        if not isinstance(lgr, logging.Logger):
            continue
        # Only re-attach if no FileHandler exists yet
        has_file_handler = any(
            isinstance(h, logging.FileHandler) for h in lgr.handlers
        )
        if not has_file_handler and lgr.handlers:
            fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
            fh.setFormatter(formatter)
            lgr.addHandler(fh)