import os
import csv
import pytest
from utils.logger import get_logger

logger = get_logger("FileReader")

def get_uploaded_file_path(file_name):
    """
    Search for the file inside 'report/test_data/' dynamically.
    Builds the path dynamically.
    Raises a clear error if the file does not exist.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if not file_name.endswith('.csv'):
        file_name += '.csv'
        
    primary_path = os.path.join(base_dir, "report", "test_data", file_name)
    fallback_path = os.path.join(base_dir, "test_data", file_name) # Fallback because current setup uses test_data/
    
    if os.path.exists(primary_path):
        return primary_path
    elif os.path.exists(fallback_path):
        return fallback_path
    else:
        pytest.fail(f"Uploaded file '{file_name}' does not exist in 'report/test_data/' or 'test_data/'. Please ensure it is placed correctly.")

def get_attribute_value_from_file(file_name, attribute_name):
    """
    Reads the file dynamically and returns a non-null value for the given attribute.
    """
    file_path = get_uploaded_file_path(file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        actual_header = None
        if reader.fieldnames:
            for fn in reader.fieldnames:
                if fn.strip().lower() == attribute_name.strip().lower():
                    actual_header = fn
                    break
        
        if actual_header:
            for row in reader:
                val = row.get(actual_header)
                if val and str(val).strip() != "":
                    return str(val).strip()
                    
    pytest.fail(f"Could not find any valid non-null value for column '{attribute_name}' in {file_path}")

def get_business_key_from_file(file_name):
    """
    Reads the file dynamically and returns the first column name as the business key.
    """
    file_path = get_uploaded_file_path(file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers and len(headers) > 0:
            return headers[0]
            
    pytest.fail(f"Could not determine the first column from the uploaded file {file_path}.")
