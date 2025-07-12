# Twitch Stream Monitor

A lightweight Python script that watches your favorite Twitch channels and automatically opens their streams in your default web browser when they go live. Designed for continuous, hands-off monitoring with built-in OAuth token management.

---

## Features

* 🔄 **Infinite Polling**: Runs in an endless loop, checking the Twitch API at set intervals.
* 🔑 **OAuth Token Handling**: Fetches a Client Credentials token on first run and refreshes it upon expiration.
* 🌐 **Auto-Launch Streams**: Opens new live streams in your system’s default browser.
* 🔁 **Stream Reopening**: Detects when channels go offline and resets them so they open again on return.
* ⚙️ **Easy Configuration**: Customize channel list, polling frequency, and `.env` file path.
* 📚 **API Documentation**: Uses the Twitch Helix Get Streams endpoint. See the full API reference at [https://dev.twitch.tv/docs/api/reference](https://dev.twitch.tv/docs/api/reference).

---

## Prerequisites

1. **Python 3.6+**
2. **pip**
3. A registered Twitch application (to obtain `CLIENT_ID` and `CLIENT_SECRET`)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start

1. **Register a Twitch App**

   * Visit the [Twitch Developer Console](https://dev.twitch.tv/console/apps).
   * Create an application and save its **Client ID** and **Client Secret**.

2. **Clone the Repo**

   ```bash
   ```

git clone [https://github.com/danielplaskur/Automation.git](https://github.com/danielplaskur/Automation.git)
cd Automation/Twitch

````

3. **Generate the `.env_twitch` Template**

   ```bash
python twitch_monitor.py
````

This creates a `.env_twitch` file in your home directory.

4. **Edit `.env_twitch`**

   ```dotenv
   ```

CLIENT\_ID=your\_client\_id
CLIENT\_SECRET=your\_client\_secret
USER\_LOGINS=channel1,channel2,channel3
ACCESS\_TOKEN=

````

5. **Run the Monitor**

   ```bash
python twitch_monitor.py
````

---

## How It Works

1. Loads credentials from `~/.env_twitch` (or your custom `env_path`).
2. Requests an OAuth token if none exists, or refreshes on 401 errors.
3. Polls the Twitch Helix **Get Streams** endpoint every 60 seconds by default.
4. Opens any newly live channels in your browser.
5. Tracks open streams and will open them again after they go offline and return.

### Customizing Poll Interval

Adjust the sleep duration at the bottom of `twitch_monitor.py`:

```python
# Wait X seconds before next poll
time.sleep(60)
```

---

## Configuration Variables

| Name            | Purpose                                    |
| --------------- | ------------------------------------------ |
| `CLIENT_ID`     | Your Twitch application Client ID.         |
| `CLIENT_SECRET` | Your Twitch application Client Secret.     |
| `USER_LOGINS`   | Comma-separated Twitch usernames to watch. |
| `ACCESS_TOKEN`  | Auto-populated OAuth token.                |

---

## Troubleshooting

* **401 Unauthorized**: Ensure `CLIENT_ID` and `CLIENT_SECRET` are correct; script auto-refreshes token.
* **No Streams Detected**: Confirm channel names and their live status.
* **Browser Fails to Open**: On Linux, replace `open` with `xdg-open` in the script.

---

## License

MIT License — see [LICENSE](../LICENSE).

---

*Enjoy continuous Twitch monitoring!*
