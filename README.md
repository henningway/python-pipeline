# Python Pipeline

Provides a simple API for running an object through a sequence of computations ("pipes"). Think of Unix pipelines. Works with async pipes!

Inspired by the [pipeline implementation](https://github.com/laravel/framework/blob/7.x/src/Illuminate/Pipeline/Pipeline.php) of the [Laravel framework](https://laravel.com/).

## Installation

Copy [pipeline.py](pipeline.py) to your project.

## Usage

Here is a basic example.

```python
pipe('NIAM').through([
    Reverse,
    lambda s, next: next(s.lower()),
    Wrap('__')
]).run()
```

Pipes are provided as list and can be function or class based. Class based pipes have to have a handle method. Both function based pipes and the handle method on class based pipes receive two parameters: the data from the previous pipe and a next-function, that has to be called to hand over to the next pipe. In the example *Reverse* and *Wrap* are examples of class based pipes.

```python
class Reverse(Pipe):
    def handle(self, content, next):
        return next(content[::-1])


class Wrap(Pipe):
    def __init__(self, wrapper_string: str):
        self.wrapper_string = wrapper_string

    def handle(self, content, next):
        return next(self.wrapper_string + content + self.wrapper_string)
```

More examples (including how to use with async pipes) at the bottom of [pipeline.py](pipeline.py).

## Documentation

See docstring on the Pipeline class in [pipeline.py](pipeline.py).

## Tests

Run
```
python pipeline.py
```
from the command line. If you get some text output and no errors - it works.
