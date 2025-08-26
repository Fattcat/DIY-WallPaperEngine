import time
import vlc
import win32gui
import win32con
import yt_dlp

# === Nastav si svoj YouTube link tu ===
VIDEO_URL = "https://www.youtube.com/watch?v=BNG8B5g6lGg"

# === Nájdi WorkerW (pre tapetu) ===
def get_workerw():
    progman = win32gui.FindWindow("ProgMan", None)
    win32gui.SendMessageTimeout(progman, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000)

    workerws = []
    def enum_callback(hwnd, lparam):
        p = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
        if p:
            workerw = win32gui.FindWindowEx(0, hwnd, "WorkerW", None)
            if workerw:
                lparam.append(workerw)
        return True
    win32gui.EnumWindows(enum_callback, workerws)
    return workerws[0] if workerws else None

# === Získaj priamu URL z YouTube ===
def get_youtube_url(url):
    try:
        ydl_opts = {
            'format': 'best[height<=1080][ext=mp4]/best[ext=mp4]/best',
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"Chyba pri získavaní URL: {e}")
        return None

# === Hlavný kód ===
def main():
    print("Hľadám plochu (WorkerW)...")
    workerw = get_workerw()
    if not workerw:
        print("❌ Nepodarilo sa nájsť plochu (WorkerW).")
        input("Stlač ENTER pre ukončenie...")
        return

    print("Získavam stream z YouTube...")
    media_url = get_youtube_url(VIDEO_URL)
    if not media_url:
        print("❌ Nepodarilo sa získať video stream.")
        input("Stlač ENTER pre ukončenie...")
        return

    # Dôležité: Namiesto --video-wallpaper použijeme bežný režim, ale skryjeme okno
    # Pretože --video-wallpaper často blokuje zvuk
    print("Spúšťam VLC s audio podporou...")
    instance = vlc.Instance(
        "--no-xlib",
        "--loop",
        "--verbose=0",
        "--audio",              # ✅ Vynúti zapnutie zvuku
        "--aout=directsound",   # ✅ Windows audio výstup
        "--volume=80",          # 80% hlasitosti
        "--video-on-top",       # Video bude pod plochou, ale zvuk ide
    )

    player = instance.media_player_new()
    media = instance.media_new(media_url)
    player.set_media(media)

    # Nastavime video na tapetu (WorkerW)
    player.set_hwnd(workerw)

    # Zapneme zvuk ručne
    player.audio_set_volume(80)
    print("🔊 Zvuk nastavený na 80%")

    # Spustíme
    print("✅ Video spustené na tapete! Zvuk by mal ísť.")
    player.play()

    # Kontrola, či sa video naozaj hraje
    time.sleep(2)
    if player.is_playing():
        print("🟢 Video prehráva.")
    else:
        print("🟡 Video sa nespustilo – skontroluj URL alebo pripojenie.")

    # Beží donekonečna
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Zastavujem prehrávanie...")
        player.stop()

if __name__ == "__main__":
    main()
