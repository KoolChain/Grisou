#!/usr/bin/env python 

import asyncio
import sys
import stream


async def process_in_term():
    process = await asyncio.create_subprocess_exec(*["xterm", "-e", "./example.sh"])
    print("Create called")
    return await process.wait()


async def interact():
    read = await stream.ainput(prompt="Koi", loop=loop),
    print("Received {}".format(read))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    rc = loop.run_until_complete(asyncio.wait([
        process_in_term(),
        process_in_term(),
        interact(),
    ]))
    loop.close()

