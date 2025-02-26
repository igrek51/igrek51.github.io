# The Pitfalls in Async Python
Async Python is great - until you get to the point where it's not. And when it fails, it fails hard.
One **accidental blocking call** is all it takes to freeze your entire application.

## Accidental Blocking Call
> It's easy to inadvertently introduce blocking calls into async code, which can freeze your entire application. This could might as well been in your async endpoint in something like FastAPI. It applies to using certain HTTP or database libraries, or even simple file operations.

We often rely on third-party libraries, but you can't vouch for every single one of them, assuming they handle async properly.
It once happened to me and it was a nightmare. I spent a week on debugging a production issue that made my FastAPI server unstable.
The server had async endpoints. I used third-party libraries inside, but I didn't know that one of them was badly written and in case of a database disconnection it would block the coroutine for a long time, effectively freezing the entire async loop.
The worst part is that when the app locks up like that, it becomes completely unresponsive. No logs, no errors - just silence. You can't even see what's going on or check where it's stuck because it's not responding! It even stops responding to liveness probes, trigerring endless restarts. It was a nightmare to diagnose. One time it happens and believe me, you're gonna hate it. That's why I avoid it whenever I can.

## Coroutine Timeout
Here's another surprising example.
Imagine using a poorly written library that blocks a coroutine for a long time:
```python
import time

async def cant_stop_me():
    time.sleep(10)
```

You might try to set a timeout to continue execution after 1 second using the seemingly convenient
[`asyncio.timeout`](https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout):
```python
import asyncio

async def main():
    async with asyncio.timeout(1):
        await cant_stop_me()

asyncio.run(main())
```

Wrong!
The code above will still run 10 seconds and `asyncio.timeout` has no power here.
That's how asyncio works, it can't interrupt a synchronous call because it just handed over the whole control to it
and now it waits until the naughty coroutine let go of the control.
If you call something synchronous in an async thread, it will block, and there's nothing you can do.
Even `asyncio.timeout` won't work or any kind of cancelling the coroutine,
because in asyncio there's only one thread, and this single thread is fully occupied by the coroutine.

The solution is to wrap the blocking call in a separate thread and await it asynchronously,
preventing the main async loop from being blocked:
```python
import asyncio

def blocking_func():
    return asyncio.run(cant_stop_me())

async def main():
    try:
        async with asyncio.timeout(1):
            await asyncio.to_thread(blocking_func)
    except TimeoutError:
        print('Timeout')

asyncio.run(main())
```

## Controlling the size of async chunks
Many async Python developers might not realize the importance of controlling the size of async chunks.
Async Python executes code in chunks, moving from one `await` keyword to another.
The async loop resumes the first running coroutine and waits until it encounters next `await`,
which is the only point where control returns to the async loop, allowing it to switch to executing other coroutines.

![](../assets/journal/concurrent-async-execution.png)
/// caption
In a Pyhton async loop, coroutines are executed alternately but sequentially in small chunks.
///

Imagine running a fully async Python server, like FastAPI, on Kubernetes.
You typically configure liveness probes to periodically check server health.

```python
app = fastapi.FastAPI()

@app.get('/live')
async def live_endpoint():
    return {'live': True}

@app.post('/api/call')
async def heavy_endpoint():
    return await long_computation()
```

The default timeout for a liveness probe is 1 second,
meaning your app must respond within that time. Otherwise, it's going to be killed by Kubernetes.
This isn't usually a problem for multithreaded apps, which can easily respond to lightweight live endpoints regardless of load.

The problem begins with async Python.
To give a live endpoint a chance to be processed while the server is busy,
you must ensure that **any** async chunk lasts no longer than one second.
How can you be sure of this? Are you aware of this when writing async Python code?
Now, you'd rather start dividing your code into functions according to their execution time, adding more `await` keywords.
Suddenly, you spend considerable time answering questions like:

- What's the time complexity of this function?
- How long will it run on production data?
- How large will the input be? What's the worst case?
- How fast are the CPUs on the server?
- Will it fit in a 1-second chunk?
- Even if it lasts `600ms`, what if there are many concurrent requests? The async loop might schedule them sequentially: `heavy_endpoint + heavy_endpoint + live_endpoint`, preventing the live endpoint from responding within 1 second, causing the app to be restarted.

Now, think about multithreading, where you don't have such problems.
Or think about the Go programming language, where its fabulous concurrency works like a charm without such concerns.

## The Risks of Async Python
- Accidental Blocking Calls - inadvertent blocking call can freeze your entire application.
- Steep Learning Curve - Understanding the event loop, Coroutines, Tasks, Futures, and non-blocking operations takes time.
- Increased Code Complexity
- Debugging Challenges

## Reference snippets
If you're struggling with the correct syntax in async Python, here are some reference snippets:

- Running async function in a sync context:
```python
async def fun(args):
    pass

def main(args):
    result = asyncio.run(fun(args))
```

- Running sync function in an async context without blocking the async loop:
```python
def fun(args):
    pass

async def main(args):
    result = await asyncio.to_thread(fun, args)
```

- Running async function in an async context:
```python
async def fun(args):
    pass

async def main(args):
    result = await fun(args)
```

- Running sync function in a sync context:
```python
def fun(args):
    pass

def main(args):
    result = fun(args)
```

## Summary
You might think solutions for inadvertent blocking calls in async Python are simple:

- Use synchronous `def` endpoints in FastAPI and let them run in a thread pool
- Or use `asyncio.to_thread` to offload blocking calls.

But if we're going to use multithreading everywhere,
what's the point of using asyncio anyway?
What was wrong with good old multithreading?
And now, with Python 3.13 free-threading, it's even more debatable.
While async Python has benefits, it also comes with serious risks.

## References
- [Why I avoid async Python when I can](https://oscar-evertsson.medium.com/why-i-avoid-async-python-when-i-can-dfa383a2125c)
