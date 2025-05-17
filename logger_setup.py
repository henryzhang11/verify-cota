import logging
import os
import datetime

def setup_logging(program="app"):
    # Clean 'app.log' if it is too long.
    try:
        with open(program + ".log", 'r') as f:
            log_content = f.read()
        if len(log_content) > 100000:
            if not os.path.exists("log"):
                os.makedirs("log")
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_filename = os.path.join("log", program + f"_{timestamp}.log")
            with open(archive_filename, 'w') as archive_f:
                archive_f.write(log_content)
            with open(program + '.log', 'w') as f:
                f.write("")
            print(f"Log file cleaned and archived to {archive_filename}.")
    except FileNotFoundError:
        print("Log file " + program + "'.log' not found.")
    except Exception as e:
        print(f"An error occured: {e}.")
    # Create a root logger and set its level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Create handlers
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    file_handler = logging.FileHandler(program + '.log')
    file_handler.setLevel(logging.DEBUG)
    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # Avoid adding duplicate handlers if setup_logging is called more than once
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)