import time
import vlc
import win32gui
import win32con
import yt_dlp


VIDEO_URL = "https://www.youtube.com/watch?v=BNG8B5g6lGg"
VOLUME = 80


def get_desktop_window():
    progman = win32gui.FindWindow("ProgMan", None)

    win32gui.SendMessageTimeout(
        progman, 0x052C, 0, 0,
        win32con.SMTO_NORMAL, 1000
    )

    desktop = None

    def enum_windows(hwnd, _):
        nonlocal desktop
        shell = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
        if shell:
            workerw = win32gui.FindWindowEx(0, hwnd, "WorkerW", None)
            desktop = workerw if workerw else hwnd
            return False
        return True

    win32gui.EnumWindows(enum_windows, None)
    return desktop if desktop else progman


def get_youtube_stream(url):
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]


def main():
    print("🔍 Hľadám desktop okno...")
    desktop_hwnd = get_desktop_window()
    print(f"✅ Desktop HWND: {hex(desktop_hwnd)}")

    print("🌐 Získavam YouTube stream (android client)...")
    media_url = get_youtube_stream(VIDEO_URL)

    print("🎬 Inicializujem VLC...")
    instance = vlc.Instance(
        "--no-video-title-show",
        "--loop",
        "--quiet",
        "--audio",
        "--aout=directsound"
    )

    player = instance.media_player_new()
    media = instance.media_new(media_url)
    player.set_media(media)

    player.set_hwnd(desktop_hwnd)
    player.audio_set_volume(VOLUME)

    print("▶ Spúšťam video...")
    player.play()
    time.sleep(1)
    player.play()

    time.sleep(2)
    print("🟢 Beží:", bool(player.is_playing()))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        player.stop()


if __name__ == "__main__":
    main()
