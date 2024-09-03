# aiomultithreading:
[![PyPI version](https://badge.fury.io/py/aiomultithreading.svg)](https://badge.fury.io/py/aiomultithreading)
![PyPI - Downloads](https://img.shields.io/pypi/dm/aiomultithreading)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Tests](/aiomultithreading/actions/workflows/tests.yml/badge.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

## What is it?

**aiomultithreading** is

A concept for creating the Best Possible Utilization of threading, multiprocessing and asyncio combined into one
executor allowing the number of tasks running in parallel to be multiplied rapidly without 
having to do very many setups. 

Aiomultithreading is meant for handling super bulky tasks such as proxy-enumeration or networking
on a very large scale. This can be costly for some uneducated programmers but luckily 
this tool completely changes that by making use of not just your threads, cores or
task counts alone, No, All of them combined. This library completely changes the playing-field 
and I expect to see a few people using this for something really intense. 


With the combined help of aiomultiprocessing and aiothreading it is possible to acheieve the 
maximum amount of tasks that can be quickly ran in parallel. 

Even the default tasks per child with threading and cores will surprise you.

Even with the use of a low cpu machine when doing the math (2 processes * 4 threads * 16 tasks per thread) 
it makes a total of 128 tasks. Theses numbers can rapidly multiply when being used pc or device using a higher 
cpu count. 

This library also has compatability for winloop and uvloop right out of the box.


## FYI
- If your goals involved some form of brute-forcing that's offline, please note that Asyncio is not the best canidate for this as
you may either create unessesary threads or deadlock your program. use [hashcat](https://github.com/hashcat/hashcat) if your goal
involves grinding hahes or performing any offline brute-forcing.


# Usage:

## Dependencies

## Installing

The easiest way is to install **aiomultithreading** is from PyPI using pip:

```sh
pip install aiomultithreading
```


## Running

First, import the library.

```python
from aiomultithreading import MultiPool
import asyncio 

async def sleep(i:float):
    await asyncio.sleep(i)
    return f"slept for {i}"

async def main():
    # 2 processes and 6 threads...
    async with MultiPool(2, 6) as pool:
        # You can go extremely fast with even 500 of these stacked together...
        x = [i for i in range(5)] * 100
        print(x)
        async for text in pool.map(sleep, x):
            print(text)

if __name__ == "__main__":
    asyncio.run(main())
```


# TODO:
    - Optimize some more important parts
