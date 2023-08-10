import json
import linecache
import os
import platform
import subprocess
import sys
import time

import fpstimer
import grequests
import requests
import rich
import spotipy
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()
API_TOKEN = os.environ.get("DISCORD_AUTH")  # https://discordhelp.net/discord-token
SPOTIFY_ID = os.environ.get("SPOTIFY_ID")
SPOTIFY_SECRET = os.environ.get("SPOTIFY_SECRET")
SPOTIFY_REDIRECT = os.environ.get("SPOTIFY_REDIRECT")
CUSTOM_STATUS = os.environ.get("STATUS")
CUSTOM_IDLE_STATUS = os.environ.get("STATUS_IDLE")
LOCALLY_STORED = os.environ.get("LOCALLY_STORED")
NITRO = os.environ.get("NITRO")
SPOTIFY_FIRST = os.environ.get("SPOTIFY_FIRST")

if NITRO == "TRUE":
    CUSTOM_STATUS_EMOJI_NAME = os.environ.get("STATUS_EMOJI_NAME")
    CUSTOM_STATUS_EMOJI_ID = os.environ.get("STATUS_EMOJI_ID")
    CUSTOM_STATUS_EMOJI_IDLE_NAME = os.environ.get("STATUS_EMOJI_IDLE_NAME")
    CUSTOM_STATUS_EMOJI_IDLE_ID = os.environ.get("STATUS_EMOJI_IDLE_ID")
else:
    CUSTOM_STATUS_EMOJI_NAME = os.environ.get("STATUS_EMOJI_NAME")
    CUSTOM_STATUS_EMOJI_IDLE_NAME = os.environ.get("STATUS_EMOJI_IDLE_NAME")

SCOPE = "user-read-currently-playing"

LYRIC_UPDATE_RATE_PER_SECOND = 10  # Rate at which the program updates the number of milliseconds passed to change lyrics.
SECONDS_TO_SPOTIFY_RESYNC = 10  # Rate at which Spotify is polled for currently playing song and time. Low numbers will be more consistent but may result in ratelimiting.

TIMER = fpstimer.FPSTimer(LYRIC_UPDATE_RATE_PER_SECOND)

last_line = ""


class StatusScreen:  # working on, currently dead code
    def __init__(self):
        self.console = rich.console.Console(color_system="auto")

    def print_if_different(self, text):
        global last_line
        if text != last_line:
            self.console.print(text)
            last_line = text


def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print(f'EXCEPTION IN ({filename}, LINE {lineno} "{line.strip()}"): {exc_obj}')


def grequest_if_different(text, status, paused):
    global last_line
    if text != last_line:
        print(status)
        send_grequest(text, paused)
        last_line = text


def request_if_different(text, status, paused):
    global last_line
    if text != last_line:
        print(status)
        send_request(text, paused)
        last_line = text


def send_grequest(text, paused):
    jsondata = {
        "custom_status": {
            "text": text,
            "emoji_name": CUSTOM_STATUS_EMOJI_NAME,
        }
    }
    if NITRO == "TRUE":
        jsondata["custom_status"]["emoji_id"] = CUSTOM_STATUS_EMOJI_ID
        if paused:
            jsondata["custom_status"]["emoji_id"] = CUSTOM_STATUS_EMOJI_IDLE_ID
            jsondata["custom_status"]["emoji_name"] = CUSTOM_STATUS_EMOJI_IDLE_NAME
    req = grequests.patch(
        url="https://discord.com/api/v6/users/@me/settings",
        headers={"authorization": API_TOKEN},
        json=jsondata,
        timeout=10,
    )
    grequests.send(req, grequests.Pool(1))


def send_request(text, paused):
    jsondata = {
        "custom_status": {
            "text": text,
            "emoji_name": CUSTOM_STATUS_EMOJI_NAME,
        }
    }
    if NITRO == "TRUE":
        jsondata["custom_status"]["emoji_id"] = CUSTOM_STATUS_EMOJI_ID
        if paused:
            jsondata["custom_status"]["emoji_id"] = CUSTOM_STATUS_EMOJI_IDLE_ID
            jsondata["custom_status"]["emoji_name"] = CUSTOM_STATUS_EMOJI_IDLE_NAME
    requests.patch(
        url="https://discord.com/api/v6/users/@me/settings",
        headers={"authorization": API_TOKEN},
        json=jsondata,
        timeout=10,
    )


def clear():  # working on, currently dead code
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


def status_screen():  # working on, currently dead code
    console = rich.console.Console(color_system="auto")
    console.print(
        "┌─────"
        "[link=https://www.willmcgugan.com]discord-status-lyric-linker[/link]"
        "─────┐"
    )


def main(last_played_song, last_played_line, song, lyrics, rlyrics):
    try:
        start = time.time()

        # IF NO SONG IS PLAYING
        if not song:
            if last_played_line == "NO SONG":
                TIMER.sleep()
                return "", "NO SONG"
            request_if_different(
                CUSTOM_IDLE_STATUS, "DISCORD: NOT CURRENTLY LISTENING UPDATE", True
            )
            TIMER.sleep()
            return "", "NO SONG"

        current_time = song["progress_ms"]
        song_length = song["item"]["duration_ms"]
        song_name = song["item"]["external_ids"]["isrc"]
        # artist_name = song["item"]["artists"][0]["name"]
        # formatted_currently_playing = f"{song_name} -- {artist_name}"

        # IF THERE ARE NO LYRICS
        if lyrics["error"] or lyrics["syncType"] == "UNSYNCED":
            # RESERVE LYRICS
            if rlyrics is not False and "lines" in rlyrics and not rlyrics["error"]:
                next_line = get_next_line(rlyrics, current_time, song_length)
                if next_line == "♪" and CUSTOM_STATUS_EMOJI_NAME != "":
                    grequest_if_different("", "", False)
                elif (
                    last_played_line != next_line
                ):  # no need to update if the line hasn't changed.
                    if SPOTIFY_FIRST == "FALSE":
                        grequest_if_different(
                            next_line,
                            "DISCORD: NEW LYRIC LINE (RESERVED / SPOTIFY)",
                            False,
                        )
                    elif SPOTIFY_FIRST == "TRUE":
                        grequest_if_different(
                            next_line,
                            "DISCORD: NEW LYRIC LINE (RESERVED / APPLE MUSIC)",
                            False,
                        )
                    last_played_line = next_line
            else:
                if (
                    last_played_line == "NO LYRICS"
                    and song_name == last_played_song
                    or last_played_line == "PAUSED OR NOT PLAYING"
                    and song_name == last_played_song
                ):
                    TIMER.sleep()
                    return song_name, last_played_line
                grequest_if_different(CUSTOM_STATUS, "DISCORD: NO SYNCED LYRICS", False)
                last_played_line = "NO LYRICS"
                TIMER.sleep()
                return song_name, last_played_line

        else:
            next_line = get_next_line(lyrics, current_time, song_length)
            if next_line == "♪" and CUSTOM_STATUS_EMOJI_NAME != "":
                grequest_if_different("", "", False)
            elif (
                last_played_line != next_line
            ):  # no need to update if the line hasn't changed.
                if SPOTIFY_FIRST == "FALSE":
                    grequest_if_different(
                        next_line, "DISCORD: NEW LYRIC LINE (APPLE MUSIC)", False
                    )
                elif SPOTIFY_FIRST == "TRUE":
                    grequest_if_different(
                        next_line, "DISCORD: NEW LYRIC LINE (SPOTIFY)", False
                    )
                last_played_line = next_line
        TIMER.sleep()
        end = time.time()
        milliseconds = (end - start) * 1000
        song["progress_ms"] += milliseconds
        return song_name, last_played_line
    except Exception:
        PrintException()


def get_next_line(lyrics, current_time, song_length):
    try:
        min_time = 100000000
        next_line = ""
        closest_line = 0
        if "lines" in lyrics.keys():
            count = 0
            for line in lyrics["lines"]:
                milliseconds_past_line = current_time - round(
                    float(line["startTimeMs"])
                )
                if milliseconds_past_line < min_time and milliseconds_past_line > 0:
                    min_time = milliseconds_past_line
                    next_line = line["words"]
                    closest_line = count
                count += 1
            if closest_line < count - 1:
                line_ahead = lyrics["lines"][closest_line + 1]
                line_current = lyrics["lines"][closest_line]
                if "endTimeMs" in line_ahead.keys() and (
                    round(float(line_current["endTimeMs"])) != 0.0
                    and current_time > round(float(line_current["endTimeMs"]))
                ):
                    timebetween = round(float(line_current["endTimeMs"])) - round(
                        float(line_ahead["startTimeMs"])
                    )
                    if timebetween < -3000:
                        next_line = "♪"
            if "endTimeMs" in lyrics["lines"][len(lyrics["lines"]) - 1].keys():
                last_lyric = round(
                    float(lyrics["lines"][len(lyrics["lines"]) - 1]["endTimeMs"])
                )
                if last_lyric != 0.0 and current_time > last_lyric:
                    next_line = "♪"
            first_lyric = round(float(lyrics["lines"][0]["startTimeMs"]))
            if current_time <= first_lyric:
                next_line = "♪"
        return next_line
    except Exception:
        PrintException()


def on_new_song(sp, last_played):
    print("SPOTIFY: LISTENING REQUEST MADE")
    current_song = sp.current_user_playing_track()
    if current_song is None:
        return False, False, False, False
    isrc = current_song["item"]["external_ids"]["isrc"]
    if isrc == last_played and last_played != "":
        return current_song, False, False, isrc
    track_id = current_song["item"]["uri"].split(":")[-1]
    current_lyrics = get_lyrics(track_id)
    reserve_lyrics = get_reserve_lyrics(isrc)
    if SPOTIFY_FIRST == "TRUE":
        return current_song, current_lyrics, reserve_lyrics, isrc
    return current_song, reserve_lyrics, current_lyrics, isrc


def local_check(path, v):
    print(f"FOUND LYRICS LOCALLY ({v})")
    with open(path, "r") as f:
        return json.load(f)


def get_lyrics(track_id):
    try:
        path = f"{os.path.dirname(os.path.realpath(__file__))}/../cache/{track_id}-spotify.json"
        if LOCALLY_STORED == "TRUE" and os.path.isfile(path):
            if SPOTIFY_FIRST == "TRUE":
                return local_check(path, "SPOTIFY")
            return local_check(path, "RESERVED / SPOTIFY")
        if SPOTIFY_FIRST == "TRUE":
            print("FETCHING LYRICS, NEW SONG (SPOTIFY)")
        elif SPOTIFY_FIRST == "FALSE":
            print("FETCHING LYRICS, NEW SONG (RESERVED / SPOTIFY)")
        data = requests.get(
            f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}", timeout=10
        ).json()
        if LOCALLY_STORED == "TRUE":
            with open(path, "w") as f:
                json.dump(data, f)
        return data
    except Exception:
        PrintException()


def get_reserve_lyrics(isrc):
    try:
        path = f"{os.path.dirname(os.path.realpath(__file__))}/../cache/{isrc}-apple-music.json"
        if LOCALLY_STORED == "TRUE" and os.path.isfile(path):
            if SPOTIFY_FIRST == "TRUE":
                return local_check(path, "RESERVED / APPLE MUSIC")
            return local_check(path, "APPLE MUSIC")
        if SPOTIFY_FIRST == "TRUE":
            print("FETCHING LYRICS, NEW SONG (RESERVED / APPLE MUSIC)")
        elif SPOTIFY_FIRST == "FALSE":
            print("FETCHING LYRICS, NEW SONG (APPLE MUSIC)")
        r = requests.get(
            f"https://beautiful-lyrics.socalifornian.live/lyrics/{isrc}", timeout=10
        )
        if r.status_code != 200:
            return _extracted_from_get_reserve_lyrics_16(path)
        try:
            rjson = r.json()
        except Exception:
            return {"error": True, "syncType": "UNSYNCED"}
        html = BeautifulSoup(rjson["Content"], "html.parser")
        data = {"error": False, "syncType": "LINE_SYNCED", "lines": []}
        lines = html.find_all("p")
        try:
            for line in lines:
                line = BeautifulSoup(str(line), "html.parser")
                if line.p.has_attr("begin"):
                    begin = timestamp_to_ms(line.p["begin"])
                    end = timestamp_to_ms(line.p["end"])
                    linedata = {
                        "startTimeMs": f"{begin}",
                        "words": f"{line.p.text}",
                        "syllables": [],
                        "endTimeMs": f"{end}",
                    }
                    data["lines"].append(linedata)
        except Exception:
            PrintException()
        if len(data["lines"]) == 0:
            return _extracted_from_get_reserve_lyrics_16(path)
        if LOCALLY_STORED == "TRUE":
            with open(path, "w") as f:
                json.dump(data, f)
        return data
    except Exception:
        PrintException()


# TODO Rename this here and in `get_reserve_lyrics`
def _extracted_from_get_reserve_lyrics_16(path):
    fakedata = {"error": True, "syncType": "UNSYNCED"}
    if LOCALLY_STORED == "TRUE":
        with open(path, "w") as f:
            json.dump(fakedata, f)
    return fakedata


def timestamp_to_ms(time):
    if ":" in time:
        time = time.split(":")
        if len(time) == 2:
            mins = int(time[0])
            seconds = mins * 60 + float(time[1])
            ms = round(seconds * 1000)
        if len(time) == 3:
            hours = int(time[0])
            mins = int(time[1])
            seconds = hours * 60 * 24 + mins * 60 + float(time[2])
            ms = round(seconds * 1000)
    else:
        seconds = float(time)
        ms = round(seconds * 1000)

    return ms


def get_spotipy():
    print("SPOTIFY: RETRIVING/REFRESHING TOKEN")
    auth = SpotifyOAuth(SPOTIFY_ID, SPOTIFY_SECRET, SPOTIFY_REDIRECT, scope=SCOPE)
    if ".cache" in os.listdir("./"):
        TOKEN = auth.get_cached_token()["access_token"]
    else:
        TOKEN = auth.get_access_token(as_dict=False)
    sp = spotipy.Spotify(TOKEN)
    return sp, auth


if __name__ == "__main__":
    song_last_played = ""
    line_last_played = ""
    lyrics = {}
    rlyrics = {}
    main_loops = 0
    sp, auth = get_spotipy()
    while True:
        try:
            if (
                main_loops % (LYRIC_UPDATE_RATE_PER_SECOND * SECONDS_TO_SPOTIFY_RESYNC)
                == 0
            ):  # we don't need to poll Spotify for the song contantly, once every 10 sec should work.
                if LOCALLY_STORED == "TRUE" and not os.path.exists(
                    f"{os.path.dirname(os.path.realpath(__file__))}/../cache"
                ):
                    os.makedirs(
                        f"{os.path.dirname(os.path.realpath(__file__))}/../cache"
                    )
                song, lyrics_state, rlyrics_state, isrc = on_new_song(
                    sp, song_last_played
                )
                if not song:
                    grequest_if_different(
                        CUSTOM_IDLE_STATUS, "SPOTIFY: NOTHING PLAYING", True
                    )
                    last_played_line = "PAUSED OR NOT PLAYING"
                if lyrics_state is not False:
                    lyrics = lyrics_state
                if rlyrics_state is not False:
                    rlyrics = rlyrics_state
                if type(song) != bool and not song["is_playing"]:
                    song = None
                    grequest_if_different(
                        CUSTOM_IDLE_STATUS, "SPOTIFY: CURRENTLY PAUSED", True
                    )
                    last_played_line = "PAUSED OR NOT PLAYING"
            song_last_played, last_played_line = main(
                isrc, line_last_played, song, lyrics, rlyrics
            )
            main_loops += 1
        except Exception as e:
            PrintException()
            print(e)
            sp, auth = get_spotipy()
