

class KeywordBuilder(object):
    def build_keyword(self, name: str, attrs: dict) -> dict:
        doc = attrs.get('Documention')
        arg_names = attrs.get('Arguments', [])
        steps = attrs.get('Steps', [])
        func_return = attrs.get('Return')

        # context = locals()

        def func(*args):
            kwargs = dict(zip(arg_names, args))
            locals().update(kwargs)
            for step in steps:
                do_step(locals(), step)
            return locals().get('func_return')

        func.__name__ = name
        func.__doc__ = doc
        return {name: func}

    def handle_keywords(self, keywords: dict) -> None:
        global functions  # fixme
        [functions.update(build_keyword(name, attrs)) for name, attrs in keywords.items()]