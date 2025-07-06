# Access Bot

Telegram bot for managing paid access with auto-kick for unsubscribed users.

## Deploy on Render

1. Push to GitHub.
2. Connect repo as a Background Worker.
3. Add env var BOT_TOKEN.
4. Ensure `runtime.txt` pins Python version.
5. Build command: `pip install --prefer-binary -r requirements.txt`
6. Done!