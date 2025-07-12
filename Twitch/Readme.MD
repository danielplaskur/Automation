# Twitch Stream Monitor

**Twitch Stream Monitor** is a lightweight Python script that continuously polls the Twitch API to check if any of your specified channels go live. When it detects a channel going live, it automatically opens their stream in your default web browser. It handles OAuth token management, auto-refreshing your access token, and will keep retrying indefinitely.

---

## Features

- 🔄 **Non-stop Monitoring**: Runs in an infinite loop, polling at regular intervals.
- 🔑 **OAuth Management**: Automatically fetches and refreshes Twitch API access tokens.
- 🌐 **Auto-Open Streams**: Opens new live streams in your default browser.
- 🔄 **Reopens Ended Streams**: Detects when channels go offline and then back online.
- ⚙️ **Configurable**: Customize channels, polling intervals, and .env path.

---

## Prerequisites

- Python 3.6 or higher
- A Twitch Application (for Client ID & Secret)

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/twitch-stream-monitor.git
   cd twitch-stream-monitor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create and configure** your `.env_twitch` file:
   Edit `.env_twitch` and set:
   ```dotenv
   CLIENT_ID=your_client_id_here
   CLIENT_SECRET=your_client_secret_here
   USER_LOGINS=channel1,channel2,channel3
   ACCESS_TOKEN=
   ```

---

## Usage

Run the monitor script:

```bash
python twitch_monitor.py
```

The script will:
1. Load your Twitch credentials from `.env_twitch`.
2. Fetch an access token if none exists.
3. Poll the Twitch API every 60 seconds (default).
4. Open any newly live streams in your default browser.
5. Remove ended streams from the “opened” list so they can reopen later.

### Customizing the Poll Interval

To change how often the script polls Twitch, modify the `time.sleep(60)` at the bottom of `twitch_monitor.py` to your desired number of seconds.

---

## Configuration

| Variable      | Description                                 |
| ------------- | ------------------------------------------- |
| CLIENT_ID     | Your Twitch application Client ID.          |
| CLIENT_SECRET | Your Twitch application Client Secret.      |
| USER_LOGINS   | Comma-separated list of Twitch usernames.   |
| ACCESS_TOKEN  | (Auto-filled) OAuth access token.           |

Ensure `.env_twitch` is located at `~/.env_twitch` or update the `env_path` variable in the script.

---

## Troubleshooting

- **Authentication Errors**: If you see a 401 error, the script will attempt to refresh your token. Ensure your CLIENT_ID/CLIENT_SECRET are correct.
- **No Streams Detected**: Verify that the usernames in `USER_LOGINS` are spelled correctly.
- **Browser Not Opening**: On Linux, replace `open` with your distro’s command (e.g., `xdg-open`).

---

## Contributing

1. Fork this repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

---

## License

MIT License. See `LICENSE` for details.

---

*Happy streaming!*
