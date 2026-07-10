import logging
import os

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
        fh = logging.FileHandler("reports/framework.log", mode="a", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger