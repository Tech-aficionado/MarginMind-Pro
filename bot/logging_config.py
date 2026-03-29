import os
import logging

def setup_logging(output_filename="trading_bot.log"):
    directory_for_logs = os.path.join(os.getcwd(), "logs")
    
    if not os.path.exists(directory_for_logs):
        os.makedirs(directory_for_logs)
        
    absolute_log_path = os.path.join(directory_for_logs, output_filename)
    
    root_application_logger = logging.getLogger()
    root_application_logger.setLevel(logging.INFO)
    
    log_message_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_system_handler = logging.FileHandler(absolute_log_path)
    file_system_handler.setFormatter(log_message_formatter)
    
    standard_output_handler = logging.StreamHandler()
    standard_output_handler.setFormatter(log_message_formatter)
    
    root_application_logger.addHandler(standard_output_handler)
    root_application_logger.addHandler(file_system_handler)
    
    logging.info("Logs are going to: %s", absolute_log_path)
