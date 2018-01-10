class AllContexts(object):
    def __init__(self, *contexts):
        self.contexts = contexts

    def __enter__(self):
        """Enter all contexts."""
        return [ctx.__enter__() for ctx in self.contexts]

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit all contexts and suppress exception
        if any context wants to suppress it.
        """
        return any([
            ctx.__exit__(exc_type, exc_value, traceback)
            for ctx in reversed(self.contexts)
        ])


if __name__ == '__main__':
    # Usage:
    class Context(object):
        """A mock context manager"""

        def __init__(self, mark):
            self.mark = mark

        def __enter__(self):
            print(f'Entering {self.mark}')
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            print(f'Exiting {self.mark}')
            return False

        def __repr__(self):
            return f'<Context {self.mark}>'

    with AllContexts(Context('a'), Context('b'), Context('c')) as ctxs:
        print(f'Current contexts: {ctxs}')
