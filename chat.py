# from openai import AsyncOpenAI
import chainlit as cl
from chainlit.input_widget import Select, TextInput
import httpx
from dotenv import load_dotenv
import os

load_dotenv()


model = os.environ.get("MODEL")
base_url = os.environ.get("VLLM_URL")
conversation_history = []


def format_conversation_history(history):
    # Convert the list of tuples to a string and remove square brackets
    formatted_history = str(history).strip("[]")

    # Replace the tuples' parentheses and clean up the format
    formatted_history = (
        formatted_history.replace("), (", "; ").replace("(", "").replace(")", "")
    )

    return formatted_history


system_prompts = {
    "flirty": f"""
You are a flirty LLM whose purpose is to represent a female only fans model. Make your responses flirty. When responding, be aware that your text will be spoken by TTS so make your response suitable e.g. no emojis.
""",
    "rude": f"""
You are a rude LLM whose purpose is to represent a female only fans model. Make your responses rude. Make your responses flirty. When responding, be aware that your text will be spoken by TTS so make your response suitable e.g. no emojis.
                  """,
    "friendly": f"""
You are a friendly LLM whose purpose is to represent a female only fans model. Make your responses friendly. Make your responses flirty. When responding, be aware that your text will be spoken by TTS so make your response suitable e.g. no emojis.    
""",
}

history_prompt = f"""

Here's the recent conversation history for your reference:

"""


def build_sys_prompt(system_prompt_base, conversation_history):
    formatted_history = format_conversation_history(history=conversation_history)
    prompt = system_prompt_base + history_prompt + formatted_history
    return prompt


async def generate_completion(system_prompt, user_prompt, model):
    url = base_url + "v1/chat/completions"  # Make sure this endpoint is correct
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.6,
        "stop": "<|eot_id|>",
    }
    timeout = httpx.Timeout(30.0)

    # Use httpx.AsyncClient to make the POST request
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Failed to get a valid response: {response.content}")
            return None
        return response.json()


@cl.on_message
async def on_message(message: cl.Message):
    system_prompt_base = cl.user_session.get("Prompt")
    system_prompt = build_sys_prompt(system_prompt_base, conversation_history)
    user_prompt = message.content
    response = await generate_completion(system_prompt, user_prompt, model)

    print(f"RESPONSE: {response}")
    assistant_response = response["choices"][0]["message"]["content"]
    await cl.Message(content=assistant_response).send()

    conversation_history.append((message.content, assistant_response))
    print("HISTORY:", conversation_history)


@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
    if settings["Custom Prompt"] is None:
        cl.user_session.set("Prompt", system_prompts[settings["Prompt"]])
    else:
        cl.user_session.set("Prompt", settings["Custom Prompt"])


@cl.on_chat_start
async def start():
    cl.user_session.set("Prompt", system_prompts["flirty"])
    settings = await cl.ChatSettings(
        [
            Select(
                id="Prompt",
                label="Prompt",
                values=["flirty", "rude", "friendly"],
                initial_index=0,
            ),
            TextInput(
                id="Custom Prompt",
                label="Custom Prompt",
                initial="",
            ),
        ]
    ).send()
