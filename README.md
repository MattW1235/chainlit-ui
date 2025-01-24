# Hosting

## Environment variables

Populate the `.env` file, you can copy `.env.example`. `MODEL` is the hugging face model name, e.g. `MattW1235/model` and `VLLM_URL` is a base url that exposes an openai compatible api such as vLLM (specifically a `v1/chat/completions`).

## Dependencies

The project uses uv. The easiest way to install uv is like this: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Or the manual approach if you prefer not to use `sh` + `curl`:

1. Install pipx using the steps for your chosen distro: https://github.com/pypa/pipx?tab=readme-ov-file#on-linux

For ubuntu this is simply:

```sh
sudo apt update
sudo apt install pipx
pipx ensurepath
```

2. Install uv: `pipx install uv`
3. Either run this command `. ~/.bashrc` or restart the terminal session.
4. Now if you type `uv` it should work (e.g. not complain about the command not being found).

## Start

Ensure you're in the `chainlit-ui` folder. The command to start the server is `uv run chainlit run chat.py`.

Note that this will stop whenever your terminal session ends, if you want it to run in the background you need to run it like this: `nohup uv run chainlit run chat.py &`
