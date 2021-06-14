import inspect
import functools


LABEL_STACK_MAP = dict()


def logaugment(logger, label, key, stacked=False, prefix='', postfix=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def make_value(label_stack, prefix, postfix):
                if label_stack:
                    return f'{prefix}{":".join(label_stack)}{postfix}'
                else:
                    return ''

            was_appended = False
            if stacked:
                label_stack = LABEL_STACK_MAP.setdefault(logger.name, [])
            else:
                label_stack = []
            if label and (not label_stack or not label_stack[-1] == label):
                was_appended = True
                label_stack.append(label)
                logger.extra[key] = make_value(label_stack, prefix, postfix)
            result = func(*args, **kwargs)
            if label and was_appended:
                label_stack.pop()
                logger.extra[key] = make_value(label_stack, prefix, postfix)
            return result
        return wrapper
    return decorator


def logaugment_parameter(logger, parameter, key, stacked=False, prefix='', postfix=''):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if len(args) > 0:
                signature = inspect.signature(func)

                def parameter_position(ordered_dict, key):
                    return list(ordered_dict).index(key)

                label = args[parameter_position(signature.parameters, parameter)]
            elif kwargs:
                label = kwargs[parameter]
            else:
                raise ValueError(f'function called without {parameter} parameter')
            logaugment_decorator = logaugment(logger, label, key, stacked, prefix, postfix)
            wrapper = functools.update_wrapper(logaugment_decorator, func)
            result = wrapper(func)(*args, **kwargs)
            return result
        return wrapper
    return decorator
