# Aiomultithreading

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



## FYI
- If your goals involved some form of brute-forcing that's offline, please note that Asyncio is not the best canidate for this.
Use hashcat if your trying to grind those kinds of things out.


# Example

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

