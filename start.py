"""Start.py.
    Intitialize the environment variables and start the bot.
"""
import os
import pathlib
import platform
import subprocess
import sys
from getpass import getpass

# N0v4 what kind of crack are you smoking?
# Anyway I fixed a lot of the code base.
# Soon gonna check if it works on Windows.


def clear():
    if platform.system() == "Windows":
        if platform.release() in {"10", "11"}:
            subprocess.run(
                "", shell=True, check=True
            )  # Needed to fix a bug regarding Windows 10; not sure about Windows 11
            print("\033c", end="")
        else:
            subprocess.run(["cls"], check=True)
    else:  # Linux and Mac
        print("\033c", end="")


def checkvenv():
    """Start a venv on linux and install packages.
    otherwise just install packages on Windows.
    """
    if platform.system() != "Windows":
        if sys.prefix == sys.base_prefix:
            makevenv()
        # trunk-ignore(bandit/B603)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True
        )
        pip_executable = pathlib.PurePath(sys.executable).parent / "pip"
        print(pip_executable)
        print(sys.executable)
    else:
        pip_executable = pathlib.PurePath(sys.executable).parent / "Scripts" / "pip.exe"
        # trunk-ignore(bandit/B603)
    subprocess.run(
        [
            pip_executable,
            "install",
            "grequests",
            "fpstimer",
            "spotipy",
            "python_dotenv",
            "gevent",
            "rich",
            "bs4",
        ],
        check=True,
    )
    clear()


# TODO Rename this here and in `venv`
def makevenv():
    print(
        "You're currently not in a venv, make sure you are. \n"
        "I'll generate a script called run.sh that should restart this in a venv, \n"
        "but before that, I'll make a venv for you. \n"
        "IMPORTANT: Make sure to run run.sh or start.py in an active venv! \n"
        "This interaction will repeat if you run start.py outside of a venv."
    )
    # trunk-ignore(bandit/B603)
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    script_contents = """#!/bin/bash
source venv/bin/activate
python start.py
    """
    with open("run.sh", "w", encoding="utf-8") as file:
        file.write(script_contents)
    # trunk-ignore(bandit/B607)
    # trunk-ignore(bandit/B603)
    subprocess.run(["chmod", "+x", "run.sh"], check=True)
    sys.exit(0)
    # subprocess.run([python_executable, "-m", "pip", "install", "--upgrade", "pip"])
    # Doesn't this break shit on windows? Better to not update pip


def create_env_file(creds: list):
    """Create a .env file based on the credentials in the creds list."""
    with open(".env", "w", encoding="utf-8") as file:
        file.write(f"DISCORD_AUTH = {creds[0]}\n")
        file.write(f"SPOTIFY_ID = {creds[1]}\n")
        file.write(f"SPOTIFY_SECRET = {creds[2]}\n")
        file.write(f"SPOTIFY_REDIRECT = {creds[3]}\n")
        file.write(f"STATUS = {creds[4]}\n")
        file.write(f"STATUS_IDLE = {creds[11]}\n")
        if creds[9] is False:
            file.write(f"STATUS_EMOJI_NAME = {creds[5]}\n")
            file.write("NITRO = FALSE\n")
        else:
            file.write(f"STATUS_EMOJI_NAME = {creds[5]}\n")
            file.write(f"STATUS_EMOJI_ID = {creds[6]}\n")
            file.write(f"STATUS_EMOJI_IDLE_NAME = {creds[7]}\n")
            file.write(f"STATUS_EMOJI_IDLE_ID = {creds[8]}\n")
            file.write("NITRO = TRUE\n")
        if creds[10] is False:
            file.write(f"LOCALLY_STORED = FALSE\n")
        else:
            file.write(f"LOCALLY_STORED = TRUE\n")
        if creds[11] is False:
            file.write(f"SPOTIFY_FIRST = FALSE\n")
        else:
            file.write(f"SPOTIFY_FIRST = TRUE\n")
        file.write(f"SPOTIFY_LYRIC_PROVIDER = {creds[12]}\n")
        file.write(f"APPLE_LYRIC_PROVIDER = {creds[13]}\n")
        if creds[14] is False:
            file.write(f"USE_CENSOR_LIST = FALSE")
        else:
            file.write(f"USE_CENSOR_LIST = TRUE")


def get_credentials():
    """Recieve credentials for the self bot.
    And later returns them as a list for .env use.
    """
    print(
        'Any input that "doesn\'t" work just have hidden echo.\n'
        "They work the same as the ones you can see, paste away."
    )
    discord_token = getpass(prompt="Enter Discord token: ")
    spotify_client_id = input("Enter Spotify application client ID: ")
    spotify_client_secret = getpass(prompt="Enter Spotify application client secret: ")
    try:
        if sys.argv[1] == "redirect":
            print(
                "Your redirect URI can literally just be http://localhost/callback"
                " it truly doesn't matter"
            )
            spotify_redirect_uri = input("Enter Spotify application redirect URI: ")
    except IndexError:
        spotify_redirect_uri = "http://localhost/callback"
    custom_status = input(
        "Enter custom status (shows when there is no lyrics/no song is playing): "
    )
    custom_idle_status = input(
        "Enter custom idle status (shows when its paused, or spotify is not being used. If you don't want to utilise this set the same status for this as you did before.): "
    )
    custom_status_emoji = input("Do you want to use custom emoji? (y/n): ")
    if custom_status_emoji.lower() == "y":
        nitro = input("Do you want to use custom emoji (nitro only)? (y/n): ")
        nitro = nitro.lower() == "y"
        if not nitro:
            print("This is the emoji that will be used for the status.")
            status_emoji_name = input("Enter emoji name for status: ")
            status_emoji_id = ""
        else:
            print(
                "This is the emoji that will be used for the status.\nKeep empty for none and to enable ♪\n"
                "Emoji ID is required for custom emojis."
            )
            status_emoji_name = input("Enter emoji name for status (do not include the ':' on either side): ")
            status_emoji_id = input("Enter emoji ID for status: ")
            print(
                "This is the emoji that will be used for the status WHEN IDLE. (If you want the same always just enter the same values as before.)\nKeep empty for none and to enable ♪\n"
                "Emoji ID is required for custom emojis."
            )
            status_emoji_idle_name = input("Enter emoji name for idle status (do not include the ':' on either side): ")
            status_emoji_idle_id = input("Enter emoji ID for idle status: ")
    else:
        nitro = False
        status_emoji_name = ""
        status_emoji_id = ""
    spotify_lyric_provider = input("Do you want a custom Spotify lyrics provider? (y/n): ")
    if spotify_lyric_provider.lower() == "y":
        spotify_lyric_provider = input("Enter the full URL (no trailing /): ")
    else:
        spotify_lyric_provider = "https://spotify-lyric-api-984e7b4face0.herokuapp.com"
    apple_lyric_provider = input("Do you want a custom Apple lyrics provider? (y/n): ")
    if apple_lyric_provider.lower() == "y":
        apple_lyric_provider = input("Enter the full URL (no trailing /): ")
    else:
        apple_lyric_provider = "https://beautiful-lyrics.socalifornian.live"
    use_censor_list = input("Do you want to use a censor list (censor.txt)? (y/n): ")
    if use_censor_list.lower() == "y":
        use_censor_list = True
    else:
        use_censor_list = False
    locally_stored = input("Do you want to store lyrics locally once the song is listened to? This is recommended for speed and lack of API spamming (stops ratelimiting being so likely) (y/n): ")
    locally_stored = locally_stored.lower() == "y"
    spotify_first = input("Do you want to use Spotify's lyrics first? (If you select no, it will use Apple Musics lyrics first, and Spotify's secondarily) (y/n): ")
    spotify_first = spotify_first.lower() == "y"

    return [
        discord_token,
        spotify_client_id,
        spotify_client_secret,
        spotify_redirect_uri,
        custom_status,
        status_emoji_name,
        status_emoji_id,
        status_emoji_idle_name,
        status_emoji_idle_id,
        nitro,
        locally_stored,
        custom_idle_status,
        spotify_first,
        spotify_lyric_provider,
        apple_lyric_provider,
        use_censor_list,
    ]


def main():
    """Start the self bot.
    and generates a .env file if it doesn't exist and runs bot.py with credentials given.
    """
    if not os.path.isfile(".env"):
        create_env_file(get_credentials())
    if not os.path.exists('cache'):
        os.makedirs('cache')

    checkvenv()
    clear()
    print("Initialized, starting...")
    while True:
        try:
            if platform.system() == "Windows":
                # trunk-ignore(bandit/B603)
                with subprocess.Popen([sys.executable, "bot\\bot.py"]) as process:
                    process.wait()
            else:
                # trunk-ignore(bandit/B603)
                with subprocess.Popen([sys.executable, "bot/bot.py"]) as process:
                    process.wait()

            print("Restarting because script crashed...")
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == "__main__":
    main()
