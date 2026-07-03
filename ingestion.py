import casparser
import tempfile
import os

def process_cas_file(file_bytes, password):
    """
    Takes raw file bytes from the web app, writes them temporarily,
    extracts the data, and wipes the physical file.
    """
    tmp_path = None
    try:
        # Create a temporary file on the hard drive
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        # Extract Python object for the database
        cas_data = casparser.read_cas_pdf(tmp_path, password)
        
        # Extract CSV text for the download button
        csv_data = casparser.read_cas_pdf(tmp_path, password, output="csv")
        
        return cas_data, csv_data

    except Exception as e:
        raise e
        
    finally:
        # Security sweep: delete the physical file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)