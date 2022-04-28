import functools
import logging

import logaugment
import settings


logaugment_operation = functools.partial(
    logaugment.logaugment, key='operation', prefix='[', postfix='] '
)
logaugment_parameter_operation = functools.partial(
    logaugment.logaugment_parameter, key='operation', prefix='[', postfix='] '
)
logaugment_ib_name_parameter_operation = functools.partial(
    logaugment_parameter_operation, parameter='ib_name'
)


logFormatter = logging.Formatter(settings.LOG_AUGMENT_FORMAT)


def getLogger(name):
    logger = logging.getLogger(name)
    for handler in logger.handlers:
        handler.setFormatter(logFormatter)
    adapter = logging.LoggerAdapter(logger, {'operation': ''})
    return adapter
