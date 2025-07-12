#!/usr/bin/env python3
"""
Twitch Stream Monitor Script (Non-stop Version)

This script continuously monitors a list of Twitch channels and automatically
opens their stream pages whenever they go live. It never exits; if streams
end, it simply keeps polling and will open again when they return.
"""
import requests
import subprocess
import time
import os
import sys

# Path to the .env file containing Twitch API credentials
env_path = os.path.expanduser('~/.env_twitch')

# Ensure .env exists
if not os.path.exists(env_path):
    with open(env_path, 'w') as f:
        f.write("# .env file for Twitch API credentials\nCLIENT_ID=\nCLIENT_SECRET=\nUSER_LOGINS=\nACCESS_TOKEN=\n")
    print(f"Created new .env file at {env_path}. Please fill in your credentials.")
    sys.exit(1)


def load_env(path):
    env = {}
    with open(path, 'r') as f:
        for line in f:
            if not line.strip() or line.startswith('#') or '=' not in line:
                continue
            key, val = line.strip().split('=', 1)
            env[key] = val
    return env


def save_env(path, env):
    with open(path, 'w') as f:
        for key, val in env.items():
            f.write(f"{key}={val}\n")


def fetch_access_token(client_id, client_secret):
    resp = requests.post(
        'https://id.twitch.tv/oauth2/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
    )
    print(resp.text)  # Debugging line to see the response
    resp.raise_for_status()
    return resp.json()['access_token']


def main():
    env = load_env(env_path)
    client_id = env.get('CLIENT_ID', '')
    client_secret = env.get('CLIENT_SECRET', '')
    user_logins = [u.strip() for u in env.get('USER_LOGINS', '').split(',') if u.strip()]
    access_token = env.get('ACCESS_TOKEN', '')

    if not access_token:
        access_token = fetch_access_token(client_id, client_secret)
        env['ACCESS_TOKEN'] = access_token
        save_env(env_path, env)
        print("🆗 New ACCESS_TOKEN saved to .env")

    headers = {
        'Client-Id': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    user_param = '&'.join(f'user_login={u}' for u in user_logins)

    opened = set()

    while True:
        try:
            r = requests.get(
                f'https://api.twitch.tv/helix/streams?{user_param}',
                headers=headers
            )
            if r.status_code != 200:
                print(f"ERROR: {r.status_code} - {r.text}")
                # refresh token on auth error
                if r.status_code == 401:
                    access_token = fetch_access_token(client_id, client_secret)
                    headers['Authorization'] = f'Bearer {access_token}'
                    env['ACCESS_TOKEN'] = access_token
                    save_env(env_path, env)
                    print("🆗 Refreshed ACCESS_TOKEN and saved.")
                time.sleep(60)
                continue

            data = r.json().get('data', [])
            live_names = {s['user_name'] for s in data}

            # Open new live streams
            for name in live_names - opened:
                print(f"Detected {name} is live. Opening stream...")
                subprocess.run(['open', f'https://twitch.tv/{name}'])
                opened.add(name)

            # Remove channels that went offline
            ended = opened - live_names
            if ended:
                for name in ended:
                    print(f"{name} has ended. Will reopen when live again.")
                opened -= ended

        except Exception as e:
            print(f"Exception occurred: {e}")

        time.sleep(60)


if __name__ == '__main__':
    main()
