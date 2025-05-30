To make async API calls to Claude models using Python, you need to use the AsyncAnthropic client 1.

First, import AsyncAnthropic and create an async client 1:

python
import os
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)
1

Then use await with each API call 1:

python
async def main() -> None:
    message = await client.messages.create(
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude",
            }
        ],
        model="claude-3-5-sonnet-latest",
    )
    print(message.content)


asyncio.run(main())