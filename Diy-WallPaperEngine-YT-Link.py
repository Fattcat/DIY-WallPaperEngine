import tkinter as tk
from tkinter import messagebox
import vlc
import threading
import time
import sys

# === Závislosti ===
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

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showerror("Chyba", "Nainštalujte Pillow:\npip install pillow")
    sys.exit(1)

# === Globálne premenné ===
player = None
instance = None
is_playing = False
transparency_level = 0.7  # pre priehľadnosť videa na tapete
WORKERW = None
background_image = None

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

    direct_url = get_youtube_url(url)
    if not direct_url:
        messagebox.showerror("Chyba", "Nepodarilo sa získať video z YouTube.")
        return

    WORKERW = get_workerw()
    if not WORKERW:
        messagebox.showerror("Chyba", "Nepodarilo sa nájsť plochu (WorkerW).")
        return

    instance = vlc.Instance("--no-xlib", "--video-wallpaper", "--loop")
    player = instance.media_player_new()
    media = instance.media_new(direct_url)
    player.set_media(media)
    player.set_hwnd(WORKERW)

    def play():
        global is_playing
        is_playing = True
        player.play()
        while is_playing:
            time.sleep(0.1)

    threading.Thread(target=play, daemon=True).start()

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

# === Minimalizácia ===
def minimize_to_tray():
    root.iconify()

# === Ukončenie ===
def on_closing():
    stop_wallpaper()
    time.sleep(0.5)
    root.destroy()

# === Nastavenie priehľadného pozadia GUI (The-RockFace.jpg s alpha=0.7) ===
def set_semitransparent_background():
    global background_image

    try:
        img = Image.open("The-RockFace.jpg").convert("RGBA")  # Otvor ako RGBA
    except FileNotFoundError:
        messagebox.showwarning("Upozornenie", "Súbor 'The-RockFace.jpg' nebol nájdený.")
        return None

    # Vytvor priehľadnú verziu (alpha = 70% z 255)
    alpha = int(255 * 0.7)  # 70 % priehľadnosti
    img = img.split()
    if len(img) == 4:
        r, g, b, _ = img
    else:
        r, g, b = img
    a = Image.new("L", r.size, alpha)  # L = grayscale pre alpha
    img_transparent = Image.merge("RGBA", (r, g, b, a))

    def resize_image(event=None):
        global background_image, resized_photo
        width = root.winfo_width()
        height = root.winfo_height()
        if width > 1 and height > 1:
            resized = img_transparent.resize((width, height), Image.Resampling.LANCZOS)
            resized_photo = ImageTk.PhotoImage(resized)
            canvas.create_image(0, 0, image=resized_photo, anchor="nw")
            # Ulož referenciu, aby nezmizla
            setattr(canvas, "img", resized_photo)

    canvas = tk.Canvas(root)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    root.bind("<Configure>", resize_image)
    root.after(100, resize_image)  # prvá aktualizácia

    return canvas

# === GUI ===
root = tk.Tk()
root.title("DIY Wallpaper Engine")
root.geometry("600x400+640+150")
root.maxsize(800, 500)
root.minsize(600, 400)

# Nastav priehľadné pozadie
canvas = set_semitransparent_background()

# Widgety nad pozadím

# Nadpis
title_label = tk.Label(root, text="DIY Wallpaper Engine", font=("Arial", 16, "bold"), fg="white", bg="#000000")
title_label.place(relx=0.5, y=30, anchor="center")

# URL vstup
frame_url = tk.Frame(root, bg="#000000", bd=1)
frame_url.place(relx=0.5, y=80, anchor="center", width=500, height=60)

tk.Label(frame_url, text="YouTube URL:", fg="white", bg="#000000", font=("Arial", 10)).place(x=10, y=5)
entry_url = tk.Entry(frame_url, font=("Arial", 10), bd=0, highlightthickness=1, highlightbackground="#555")
entry_url.place(x=10, y=25, relwidth=0.95)
entry_url.insert(0, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Ovládacie tlačidlá
frame_controls = tk.Frame(root, bg="#000000", bd=1)
frame_controls.place(relx=0.5, y=160, anchor="center")

btn_start = tk.Button(frame_controls, text="▶️ Spustiť", command=start_wallpaper, bg="#4CAF50", fg="white", width=10)
btn_start.pack(side="left", padx=5)

btn_stop = tk.Button(frame_controls, text="⏹️ Zastaviť", command=stop_wallpaper, bg="#f44336", fg="white", width=10, state="disabled")
btn_stop.pack(side="left", padx=5)

# Stav
label_status = tk.Label(root, text="⏹️ Zastavené", font=("Arial", 10), fg="lightgray", bg="#000000")
label_status.place(relx=0.5, y=220, anchor="center")

# Minimalizovať
btn_minimize = tk.Button(root, text="🗕 Minimalizovať", command=minimize_to_tray, bg="#2196F3", fg="white", width=15)
btn_minimize.place(relx=0.5, y=260, anchor="center")

# Tip
tip_label = tk.Label(root, text="💡 Tip: Skúste loop videá (napr. 'rain loop 4K')", fg="gray", bg="#000000", font=("Arial", 9))
tip_label.place(relx=0.5, y=300, anchor="center")

# Protokol
root.protocol("WM_DELETE_WINDOW", on_closing)

# Spustenie
root.mainloop()
