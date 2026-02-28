"""
utils/logger.py - a structured logging system in place of the dumb print() on terminals 

Components: 
    - structured formatter
    - file and streaam handler
    - logger name
    - log levels
    
    
"""

import logging 
from logging.handlers import RotatingFileHandler
from logging import StreamHandler
from ..config import config 
from pathlib import Path 



def setup_logger(name: str, verbose: bool = True): 
    log_dir = Path(config.LOG_DIR)
    log_dir.parent.mkdir(parents=True, exist_ok=True)    

    logger = logging.getLogger(name=name)
    logger.setLevel(level=config.LOG_LEVEL)
    # making a structured formatter 
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    
     
        
    file_handler = RotatingFileHandler(
        filename=log_dir / f"{name}.log", 
        mode="a", 
        maxBytes=5 * 1024 * 1024, 
        backupCount=5
        )
    file_handler.setFormatter(fmt=formatter)
    logger.addHandler(file_handler)
    
    if verbose: 
        stream_handler = StreamHandler()
        stream_handler.setFormatter(fmt=formatter)
        logger.addHandler(hdlr=stream_handler)

    
    return logger 
    
    