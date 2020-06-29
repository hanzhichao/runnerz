
from logz import logit
from tmp.robots.utils import parse_dollar, split_and_strip


class Step(object):
    def _parse_args(self, context: dict, *args):
        return [parse_dollar(context, arg) for arg in args]

    def _parse_kwargs(self, context: dict, **kwargs):
        return {parse_dollar(context, key): parse_dollar(context, value) for key, value in kwargs.items()}

    @logit()
    def _do_step(self, context, expr):
        if isinstance(expr, str):
            func_name, *args = expr.split()
            print('args', args)
            key = None
            if '=' in func_name:
                key, func_name = split_and_strip(func_name, '=')

            kwargs = {item.split('=', 1)[0]: item.split('=', 1)[1] for item in args if '=' in item}
            args = [item for item in args if '=' not in item]
            args = self._parse_args(context, *args)
            kwargs = self._parse_kwargs(context, **kwargs)
            func = functions.get(func_name)
            if func:
                result = func(*args, **kwargs)
                context['result'] = context['$'] = result

                if key:
                    context[key] = result
                return result


    def do_step(self, context, expr: (str, dict)):
        filters = None
        # if isinstance(expr, dict):
        #     key, expr = tuple(expr.items())[0]  # fixme
        global functions  # fixme
        if '|' in expr:
            expr, *filters = split_and_strip(expr, '|')

            print('expr', expr, 'filters', filters)

        result = self._do_step(context, expr)
        if filters:
            for expr in filters:
                do_filter(context, expr)
