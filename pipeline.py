import asyncio
from inspect import isclass, iscoroutinefunction, iscoroutine
from typing import List, Callable, Union
from functools import reduce, wraps, partial


class Pipe:
    def handle(self, content, next):
        pass


CallablePipe = Callable
PipeType = Union[CallablePipe, Pipe]


class Pipeline:
    """
    Provides a simple API for running an object through a sequence of computations ("pipes"). Think of Unix pipelines.

    Allows to write otherwise complex imperative code in a way that reveals the intent and the flow of the program.
    Pipelines are especially useful for expressing a chain of transformations of a single piece of data or a collection
    thereof. It also eliminates intermediate variables and the need for coming up with ridiculous names.

    # How
    See the bottom of this file for examples. If you are the type of person that would rather read a boring manual,
    please read on.

    Pipes are classes or objects with a "handle" method or plain functions (we will include the latter when we speak of
    handle methods for convenience). The handle method receives two arguments: "content" and "next". content is the data
    that is passed into the pipeline or from the previous pipe. The pipe will perform any transformation and then pass
    the result to the "next" function. "next" is just a closure that is responsible for invoking the next pipe, hence
    the name.

    # Implementation details
    The implementation is really straight forward, except for one detail: the "next" function and how it is produced.
    It might help to hint that it is a deeply nested closure, where each layer of "next" closes over subsequent pipes
    (to be more precise: their handle function) each wrapped by their own "next" function. One might call it a
    matryoshka of some sorts. Or a stack.

    The construction of the matryoshka is performed by reducing the pipeline with a pack function, that really does
    nothing other than putting a thin layer of "next" around each pipe. List of pipes in, nested closure out.

    Note that the packing is deferred until the moment where the client actually requests the result. This allows to
    assemble the pipeline in parts and pass it around in between and even to throw it away if you feel evil enough!

    # Why "next"?
    A simpler version of a pipeline doesn't require a "next" function. But it lacks one capability: when something goes
    wrong there is no way for the pipe to signal to the pipeline that it should stop execution but return the result
    nonetheless.

    As an analogy, think of an assembly line: When a machine notices something fishy about the intermediate product it
    processes, then it can do one of two things: (1) Stop execution and throw away the product. This is analogous to
    throwing an exception - the intermediate data is lost and the client code only receives an exception with a message.
    This is possible even in simple pipelines. (2) Finish processing the product and signal the line to halt. This is
    analogous to not calling the "next" function in a more advanced pipeline, but still returning the transformed data.

    Take for instance web middleware: Multiple middlewares receive a request in sequence and collectively produce a
    response. A middleware responsible for authentication might decide that an attempt to login was invalid. It will
    add a 401 status header to the response and return prematurely without continuing the pipeline. In fact, this is
    how Laravel uses pipelines, and this implementation was inspired by theirs.

    # Refactor to pipelines
    Refactoring an existing script into a pipeline is a two step process:
    (1) Identify and extract logical groups of code into pipes (complex logic: class, simple logic: function).
    (2) Replace original code with pipeline, which receives the pipes in sequence.
    """

    def __init__(self, passable=None):
        self.pipes = []
        self.passable = passable

    def through(self, pipes: List[PipeType]):
        self.pipes.extend(pipes)
        return self

    def prepare(self):
        def resolve_handler(pipe: PipeType):
            if isclass(pipe):
                pipe = pipe()

            if hasattr(pipe, 'handle'):
                return pipe.handle

            return pipe

        pipeline = [resolve_handler(pipe) for pipe in self.pipes]

        # serves as initial "next" function
        def identity(x):
            return x

        def pack_next(stack, pipe):
            def next(carry):
                return pipe(carry, stack)

            return next

        pipeline = reduce(pack_next, pipeline[::-1], identity)

        return pipeline

    def run(self):
        pipeline = self.prepare()
        return pipeline(self.passable)

    async def run_async(self):
        pipeline = self.prepare()
        result = pipeline(self.passable)

        while iscoroutine(result):
            result = await result

        return result


def pipe(passable=None):
    return Pipeline(passable)


# example usage
if __name__ == '__main__':
    class Reverse(Pipe):
        def handle(self, content, next):
            return next(content[::-1])


    class Wrap(Pipe):
        def __init__(self, wrapper_string: str):
            self.wrapper_string = wrapper_string

        def handle(self, content, next):
            return next(self.wrapper_string + content + self.wrapper_string)


    class HelloProducer(Pipe):
        def handle(self, _, next):
            return next('hello')


    class Wait500(Pipe):
        async def handle(self, content, next):
            await asyncio.sleep(0.5)
            return next(content)


    def example_basic():
        # read "Pipe object through sequence of tasks, then do something with the result."
        result = pipe('NIAM').through([
            # class pipe
            Reverse,

            # function pipe
            lambda s, next: next(s.lower()),

            # object pipe (pre-initialized class pipe - useful if pipe has dependencies)
            Wrap('__')
        ]).run()
        print(result)


    def example_no_input():
        # first pipe produces data
        result = pipe().through([HelloProducer, Wrap('__')]).run()
        print(result)

    async def example_async_pipes():
        result = await pipe('cnysa').through([Wait500, Wrap('__'), Wait500, Reverse]).run_async()
        print(result)

    example_basic()
    example_no_input()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(example_async_pipes())
