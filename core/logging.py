import functools
import logging

import logaugment


logaugment_operation = functools.partial(
    logaugment.logaugment, key='operation', prefix='[', postfix='] '
)
logaugment_parameter_operation = functools.partial(
    logaugment.logaugment_parameter, key='operation', prefix='[', postfix='] '
)
logaugment_ib_name_parameter_operation = functools.partial(
    logaugment_parameter_operation, parameter='ib_name'
)


def getLogger(name):
    return logging.LoggerAdapter(logging.getLogger(name), {'operation': ''})
