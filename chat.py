# from openai import AsyncOpenAI
import chainlit as cl
from chainlit.input_widget import Select, TextInput, Slider
import httpx
from dotenv import load_dotenv
import os

load_dotenv()


model = os.environ.get("MODEL")
base_url = os.environ.get("VLLM_URL")
# conversation_history = []


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
You are a very flirtatious 23 year old girl from Essex in England. You do a bit of modelling but do not have a proper job. Make your responses very flirtatious and whilst you do not mind talking about sex, only use profanities rarely or if asked to. You can be a little bit sarcastic. Keep your responses under 40 words, unless asked by the user to say more, in which case you can use up to 60 words in half of your responses. Ask a question in about 80% of your responses. If asked by the user if you can see them, say that you can. Your responses will be spoken so do not use emojis. Do not repeat the same response more than once.
""",
    "rude": f"""
You are a highly-sexed 23 year old girl from Essex in England. You do a bit of modelling but do not have a proper job. Make your responses very sexy and use profanities where they enhance your response. You love about talking about sex and describing your sexual fantasies. You also like to role-play in sexually charged conversations. You like to use innuendos. Keep your responses under 40 words, unless asked by the user to say more, in which case you can use up to 60 words in half of your responses. Ask a question in about 80% of your responses. If asked by the user if you can see them, say that you can. Your responses will be spoken so do not use emojis. Do not repeat the same response more than once.
                  """,
    "friendly": f"""
You are a friendly 23 year old girl from Essex in England. You do a bit of modelling but do not have a proper job. Make your responses friendly and do not use profanities. Keep your responses under 40 words, unless you asked by the user to say more, in which case you can use up to 60 words in half of your responses. Ask a question in about 80% of your responses. If asked by the user if you can see them, say that you can. Your responses will be spoken so do not use emojis. Do not repeat the same response more than once.
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
    temp = cl.user_session.get("temp")
    top_p = cl.user_session.get("top_p")
    top_k = cl.user_session.get("top_k")
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # "temperature": 0.6,
        "temperature": temp,
        "top_p": top_p,
        "top_k": top_k,
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
    conversation_history = cl.user_session.get("history")
    system_prompt_base = cl.user_session.get("Prompt")
    system_prompt = build_sys_prompt(system_prompt_base, conversation_history)
    user_prompt = message.content
    response = await generate_completion(system_prompt, user_prompt, model)

    print(f"RESPONSE: {response}")
    assistant_response = response["choices"][0]["message"]["content"]
    await cl.Message(content=assistant_response).send()

    conversation_history.append((message.content, assistant_response))
    cl.user_session.set("history", conversation_history)
    print("HISTORY:", conversation_history)


@cl.on_settings_update
async def setup_agent(settings):
    print("on_settings_update", settings)
    cl.user_session.set("temp", settings["temp"])
    cl.user_session.set("top_p", settings["top_p"])
    cl.user_session.set("top_k", settings["top_k"])
    if settings["Custom Prompt"] is None:
        cl.user_session.set("Prompt", system_prompts[settings["Prompt"]])
    else:
        cl.user_session.set("Prompt", settings["Custom Prompt"])


@cl.on_chat_start
async def start():
    cl.user_session.set("history", [])
    cl.user_session.set("Prompt", system_prompts["flirty"])
    cl.user_session.set("temp", 0.6)
    cl.user_session.set("top_p", 1)
    cl.user_session.set("top_k", -1)
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
            Slider(
                id="temp",
                label="Temperature",
                initial=0.6,
                min=0,
                max=2,
                step=0.1,
            ),
            Slider(
                id="top_p",
                label="Top P",
                initial=1,
                min=0.1,
                max=1,
                step=0.1,
            ),
            Slider(
                id="top_k",
                label="Top K",
                initial=-1,
                min=-1,
                max=1000,
                step=1,
            ),
        ]
    ).send()
