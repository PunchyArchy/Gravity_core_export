import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
from gravity_core import  wsettings as s


# get named logger
logger = logging.getLogger(__name__)

# create handler
handler = TimedRotatingFileHandler(filename=s.sys_logs, when='D', interval=1, backupCount=15, encoding='utf-8',
                                   delay=False)

# create formatter and add to handler
formatter = Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handler to named logger
logger.addHandler(handler)

# set the logging level
logger.setLevel(logging.INFO)