import asyncio
import os

from openai import AsyncOpenAI

# Assuming 'agents' module and its components are in the same directory or PYTHONPATH
# If not, these imports will fail.
# from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled

# Placeholder for agents components if the module is not found
# This is to make the file runnable for basic checks,
# but actual LLM calls will fail without the correct 'agents' module.
class Agent:
    def __init__(self, name, instructions, model, tools):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools

class OpenAIChatCompletionsModel:
    def __init__(self, model, openai_client):
        self.model = model
        self.openai_client = openai_client

class Runner:
    @staticmethod
    async def run(agent, prompt, run_config=None):
        # This is a mock implementation
        print(f"Mock Runner: Running agent '{agent.name}' with prompt: '{prompt}'")
        # Simulate an LLM call and tool use
        if agent.tools:
            tool_name = agent.tools[0].__name__
            print(f"Mock Runner: Pretending to call tool '{tool_name}'")
            tool_result = "Mock tool result"
            print(f"Mock Runner: Tool '{tool_name}' returned: {tool_result}")
        # Simulate a haiku response as per instructions
        return type('obj', (object,), {'final_output': "Mocked haiku here,\nSun shines on the city now,\nWeather is so fine."})()

def function_tool(func):
    return func

def set_tracing_disabled(disabled):
    print(f"[debug] Tracing disabled: {disabled}")


# Configuration for Anthropic API
BASE_URL = "https://api.anthropic.com/v1/"  # Pre-filled for Anthropic
API_KEY = os.getenv("ANTHROPIC_API_KEY") or "" # You need to set this environment variable
MODEL_NAME = os.getenv("EXAMPLE_MODEL_NAME") or "claude-sonnet-4-20250514" # Defaulting to claude-sonnet-4-20250514

if not API_KEY:
    raise ValueError(
        "Please set ANTHROPIC_API_KEY via env var. EXAMPLE_BASE_URL is pre-configured for Anthropic and EXAMPLE_MODEL_NAME can be optionally set."
    )

if not BASE_URL:
    raise ValueError("BASE_URL is not set. This should be pre-filled for Anthropic.")


"""This example uses a custom provider for a specific agent. Steps:
1. Create a custom OpenAI client.
2. Create a `Model` that uses the custom client.
3. Set the `model` on the Agent.

Note that in this example, we disable tracing under the assumption that you don't have an API key
from platform.openai.com. If you do have one, you can either set the `OPENAI_API_KEY` env var
or call set_tracing_export_api_key() to set a tracing specific key.
"""
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)

# An alternate approach that would also work:
# PROVIDER = OpenAIProvider(openai_client=client)
# agent = Agent(..., model="some-custom-model")
# Runner.run(agent, ..., run_config=RunConfig(model_provider=PROVIDER))


@function_tool
def get_weather(city: str):
    print(f"[debug] getting weather for {city}")
    # In a real scenario, this might call an actual weather API
    return f"The weather in {city} is sunny."


async def main():
    # This agent will use the custom LLM provider
    agent = Agent(
        name="Assistant",
        instructions="You only respond in haikus.",
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client),
        tools=[get_weather],
    )

    # Make sure the prompt is a string
    result = await Runner.run(agent, "What's the weather in Tokyo?")
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main()) 