# -----------------------------------------------------------------------------
# Module: bot.logging_config
# Description: Centralized logging configuration for terminal and file output.
# -----------------------------------------------------------------------------

import os
import logging

def setup_logging(name="trading_bot.log"):
    """
    Configures a dual-handler logger that outputs to both the console 
    and a persistent file within the 'logs/' directory.
    """
    # Ensure the logs directory exists.
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, name)
    
    # Root logger configuration.
    l = logging.getLogger()
    l.setLevel(logging.INFO)

    # Standard format: Time - Level - Message
    f = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Handler 1: StreamHandler for real-time console feedback.
    ch = logging.StreamHandler()
    ch.setFormatter(f)
    l.addHandler(ch)

    # Handler 2: FileHandler for persistent auditing in logs/ directory.
    fh = logging.FileHandler(log_path)
    fh.setFormatter(f)
    l.addHandler(fh)

    logging.info("Bot is warming up... Logging to %s", log_path)
