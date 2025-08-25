import tkinter as tk
from tkinter import messagebox
import vlc
import threading
import time
import sys

# === Skontroluj závislosti ===
try:
    import pafy
    USE_YT_DLP = False
except ImportError:
    try:
        import yt_dlp as youtube_dl
        USE_YT_DLP = True
    except ImportError:
        messagebox.showerror("Chyba", "Nainštalujte:\npip install pafy\nalebo\npip install yt-dlp")
        sys.exit(1)

try:
    import win32gui
    import win32con
except ImportError:
    messagebox.showerror("Chyba", "Nainštalujte pywin32:\npip install pywin32")
    sys.exit(1)

# === Globálne premenné ===
player = None
instance = None
is_playing = False
transparency_level = 0.7
WORKERW = None

# === Nájdi WorkerW (desktop canvas) ===
def get_workerw():
    """Nájde handle na WorkerW – miesto, kde sa kreslia tapety"""
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
        if USE_YT_DLP:
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'quiet': True,
                'noplaylist': True,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return info['url']
        else:
            video = pafy.new(url)
            best = video.getbest(preftype="mp4")
            return best.url
    except Exception as e:
        print(f"Chyba pri získavaní URL: {e}")
        return None

# === Spustenie videa ako tapeta ===
def start_wallpaper():
    global player, instance, is_playing, WORKERW

    if is_playing:
        messagebox.showinfo("Info", "Video už prehráva!")
        return

    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Chyba", "Zadajte YouTube link!")
        return

    # Získaj priamu URL
    direct_url = get_youtube_url(url)
    if not direct_url:
        messagebox.showerror("Chyba", "Nepodarilo sa získať video z YouTube.")
        return

    # Nájdi WorkerW
    WORKERW = get_workerw()
    if not WORKERW:
        messagebox.showerror("Chyba", "Nepodarilo sa nájsť plochu (WorkerW). Reštartujte alebo skúste znova.")
        return

    # Inicializuj VLC
    instance = vlc.Instance("--no-xlib", "--video-wallpaper", "--loop", "--avcodec-hw=any")
    player = instance.media_player_new()

    media = instance.media_new(direct_url)
    player.set_media(media)

    # Dôležité: nastav video priamo na WorkerW (desktop)
    player.set_hwnd(WORKERW)

    # Spusti v samostatnom vlákne
    def play():
        global is_playing
        is_playing = True
        player.play()
        while is_playing:
            time.sleep(0.1)

    threading.Thread(target=play, daemon=True).start()

    # Aktualizuj GUI
    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    label_status.config(text="✅ Prehráva sa na tapete")

# === Zastavenie videa ===
def stop_wallpaper():
    global is_playing, player, instance
    if player:
        player.stop()
        is_playing = False
        player = None
        instance = None
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")
    label_status.config(text="⏹️ Zastavené")

# === Zmena priehľadnosti tapety (funguje cez alpha kanál WorkerW) ===
def set_transparency(val):
    global transparency_level
    transparency_level = float(val) / 100.0
    if is_playing and WORKERW:
        # Nastav priehľadnosť cez Windows API
        import win32gui
        import win32con
        style = win32gui.GetWindowLong(WORKERW, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(WORKERW, win32con.GWL_EXSTYLE, style | win32con.WS_EX_LAYERED)
        win32gui.SetLayeredWindowAttributes(WORKERW, 0, int(255 * transparency_level), win32con.LWA_ALPHA)

# === Minimalizácia GUI ===
def minimize_to_tray():
    root.iconify()

# === Ukončenie ===
def on_closing():
    stop_wallpaper()
    time.sleep(0.5)
    root.destroy()

# === GUI ===
root = tk.Tk()
root.title("DIY Wallpaper Engine")
root.geometry("600x350+640+300")
root.maxsize(610, 410)
root.minsize(600, 400)
root.configure(bg="#1e1e1e")
root.protocol("WM_DELETE_WINDOW", on_closing)

# Nadpis
tk.Label(root, text="DIY Wallpaper Engine", font=("Arial", 16, "bold"), fg="white", bg="#1e1e1e").pack(pady=10)

# URL vstup
frame_url = tk.Frame(root, bg="#1e1e1e")
frame_url.pack(pady=5, fill="x", padx=20)
tk.Label(frame_url, text="YouTube URL:", fg="white", bg="#1e1e1e").pack(anchor="w")
entry_url = tk.Entry(frame_url, width=50, font=("Arial", 10))
entry_url.pack(fill="x")
entry_url.insert(0, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # RickRoll ako demo

# Ovládacie tlačidlá
frame_controls = tk.Frame(root, bg="#1e1e1e")
frame_controls.pack(pady=10)

btn_start = tk.Button(frame_controls, text="▶️ Spustiť", command=start_wallpaper, bg="#4CAF50", fg="white", width=10)
btn_start.pack(side="left", padx=5)

btn_stop = tk.Button(frame_controls, text="⏹️ Zastaviť", command=stop_wallpaper, bg="#f44336", fg="white", width=10, state="disabled")
btn_stop.pack(side="left", padx=5)

# Priehľadnosť
frame_slider = tk.Frame(root, bg="#1e1e1e")
frame_slider.pack(pady=5)
tk.Label(frame_slider, text="Priehľadnosť tapety:", fg="white", bg="#1e1e1e").pack()
transparency_slider = tk.Scale(
    frame_slider,
    from_=30, to=100,
    orient="horizontal",
    command=set_transparency,
    bg="#333", fg="white", length=200
)
transparency_slider.set(70)
transparency_slider.pack()

# Stav
label_status = tk.Label(root, text="⏹️ Zastavené", font=("Arial", 10), fg="lightgray", bg="#1e1e1e")
label_status.pack(pady=5)

# Minimalizovať
tk.Button(root, text="🗕 Minimalizovať", command=minimize_to_tray, bg="#2196F3", fg="white").pack(pady=5)

# Tip
tk.Label(root, text="💡 Tip: Skúste loop videá (napr. 'rain loop 4K')", fg="gray", bg="#1e1e1e", font=("Arial", 9)).pack(pady=5)

# Spustenie
root.mainloop()
