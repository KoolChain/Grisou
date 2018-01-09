import main

import asyncio

if __name__ == "__main__":
    app = main.MiningApp("{device} {tag}")

    config = {
        "tag": "letag",
    }

    print(app.get_command(device="devname", **config))

    input("Test process")

    process = main.Process()
    future = asyncio.ensure_future(process.async_run("./example.sh"))
    loop = asyncio.get_event_loop() 
    loop.run_until_complete(future)

