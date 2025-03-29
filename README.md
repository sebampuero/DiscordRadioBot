# Discord Radio Bot 🎵

A simple radio discord bot

## Features

- 🎶 Stream music from various radio sources by name
- 📻 Radio station by city support

## Installation

1. Clone the repository
```bash
git clone https://github.com/sebampuero/DiscordRadioBot.git
cd discord-radio-bot
```

2. Install dependencies
```bash
poetry install --no-root
```

3. Configure the bot
- Create a `.env` file
- Add an environment variable `TOKEN=<your token>`

## Docker

1. Build the `Dockerfile`
2. Edit the `docker-compose.yaml`
3. Run
```bash
docker compose up -d
```

## Usage

Start the bot:
```bash
poetry run python src/discord_radio_bot/main.py
```

## Commands

- `!radio <radio name>` - Searches for radios by name
- `/radio-ciudad <city>` - Searches for radios in a given city

## License

[MIT](https://choosealicense.com/licenses/mit/)