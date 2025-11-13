import tkinter as tk
from tkinter import messagebox, filedialog
from urllib import response
from time import sleep
import vlc,threading, time, sys, os

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
transparency_level = 0.7
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

# === Získaj priamu URL z YouTube vo vysokej kvalite ===
def get_youtube_url(url):
    try:
        if USE_YT_DLP:
            ydl_opts = {
                'format': 'bestvideo/best',  # max kvalita
                'quiet': True,
                'noplaylist': True,
                'merge_output_format': 'mp4'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # ak je kombinovaný stream (video+audio)
                if 'url' in info:
                    return info['url']
                # ak sú oddelené, vezmi video
                elif 'formats' in info:
                    best_format = max(info['formats'], key=lambda f: f.get('height', 0))
                    return best_format['url']
        else:
            # PAFY verzia – nepoužívaj preftype="mp4"
            video = pafy.new(url)
            best = video.getbest()  # ponechaj originál
            return best.url
    except Exception as e:
        print(f"Chyba pri získavaní URL: {e}")
        return None


# === Spustenie videa ako tapeta s loop ===
def start_wallpaper():
    global player, instance, is_playing, WORKERW

    if is_playing:
        messagebox.showinfo("Info", "Video už prehráva!")
        return

    source_type = source_var.get()

    if source_type == "youtube":
        url = entry_youtube.get().strip()
        if not url:
            messagebox.showwarning("Chyba", "Zadajte YouTube link!")
            return
        direct_url = get_youtube_url(url)
        if not direct_url:
            messagebox.showerror("Chyba", "Nepodarilo sa získať video z YouTube.")
            return
        media_source = direct_url

    elif source_type == "local":
        path = entry_local.get().strip()
        if not path:
            messagebox.showwarning("Chyba", "Zadajte cestu k lokálnemu .mp4 súboru!")
            return
        if not os.path.isfile(path):
            abs_path = os.path.join(os.getcwd(), path)
            if os.path.isfile(abs_path):
                path = abs_path
            else:
                messagebox.showerror("Chyba", f"Súbor {path} neexistuje.")
                return
        media_source = path
    else:
        return

    WORKERW = get_workerw()
    if not WORKERW:
        messagebox.showerror("Chyba", "Nepodarilo sa nájsť plochu (WorkerW).")
        return

    instance = vlc.Instance("--no-xlib", "--video-on-top")
    player = instance.media_player_new()
    media = instance.media_new(media_source)
    player.set_media(media)
    player.set_hwnd(WORKERW)

    def play_loop():
        global is_playing
        is_playing = True
        player.play()
        while is_playing:
            # Ak je stav videa Ended alebo Stopped, spusti ho znova
            state = player.get_state()
            if state in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
                player.stop()
                player.play()
            time.sleep(0.2)

    threading.Thread(target=play_loop, daemon=True).start()

    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    label_status.config(text="✅ Prehráva sa na tapete")

# === Zastavenie videa ===
def stop_wallpaper():
    global is_playing, player, instance
    is_playing = False
    if player:
        player.stop()
        player.release()
        player = None
    if instance:
        instance.release()
        instance = None
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")
    label_status.config(text="⏹️ Zastavené")

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
        img = Image.open("C:\WallPaperEngineFolder\The-RockFace.jpg").convert("RGBA")  # Otvor ako RGBA
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


def DownloadAndSetGitHubIMG(root):
    import requests
    folder = r"C:\WallPaperEngineFolder" 
    #IMG_url = "https://raw.githubusercontent.com/Fattcat/DIY-WallPaperEngine/main/The-RockFace.jpg"
    IMG_url = "https://i.redd.it/3w8hx26xcw1a1.jpg"
    file_path = os.path.join(folder, "The-RockFace.jpg")
    os.makedirs(folder, exist_ok=True)

    IMG_Response = requests.get(IMG_url)
    if IMG_Response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(IMG_Response.content)
            print("IMG downloaded")
    else:
        print("error while downloading IMG from github repo")
        return

    # Vytvorenie icon.ico z The-RockFace.jpg
    img = Image.open(file_path)
    ico_path = os.path.join(folder, "icon.ico")
    img.save(ico_path, format='ICO', sizes=[(256,256)])
    root.iconbitmap(ico_path)

# === GUI ===
root = tk.Tk()

DownloadAndSetGitHubIMG(root)
#root.iconbitmap("NIGA-CORP.ico")
root.title("Wallpaper Engine")
root.geometry("600x450+640+250")
root.minsize(600, 450)
root.resizable(0,0)
#root.maxsize(800, 550)

# Nastav priehľadné pozadie
canvas = set_semitransparent_background()

# Nadpis
title_label = tk.Label(root, text="DIY Wallpaper Engine - Free Chinesse 'The Rock' Version", font=("Arial", 16, "bold"), fg="black", bg="#FFFFFF")
title_label.place(relx=0.5, y=30, anchor="center")

# === Premenná pre výber zdroja ===
source_var = tk.StringVar(value="youtube")  # default

# === YouTube URL vstup s checkboxom ===
frame_youtube = tk.Frame(root, bg="#000000", bd=1)
frame_youtube.place(relx=0.5, y=120, anchor="center", width=500, height=60)

# Radiobutton priamo v rámčeku YouTube
radio_youtube = tk.Radiobutton(frame_youtube, variable=source_var, value="youtube",
                               bg="#000000", selectcolor="#FF0000", activebackground="#000000", fg="white")
radio_youtube.place(x=10, y=22)

tk.Label(frame_youtube, text="YouTube URL:", fg="white", bg="#000000", font=("Arial", 10)).place(x=30, y=5)
entry_youtube = tk.Entry(frame_youtube, font=("Arial", 10), bd=0, highlightthickness=1, highlightbackground="#555")
entry_youtube.place(x=30, y=25, relwidth=0.90)
entry_youtube.insert(0, "https://www.youtube.com/watch?v=eCHaiEjCDFM&t=1358s")

# === Lokálne video vstup s checkboxom ===
frame_local = tk.Frame(root, bg="#000000", bd=1)
frame_local.place(relx=0.5, y=200, anchor="center", width=500, height=60)

# Radiobutton priamo v rámčeku Lokálne
radio_local = tk.Radiobutton(frame_local, variable=source_var, value="local",
                             bg="#000000", selectcolor="#EB0000", activebackground="#000000", fg="white")
radio_local.place(x=10, y=22)

tk.Label(frame_local, text="Local (.mp4):", fg="white", bg="#000000", font=("Arial", 10)).place(x=30, y=5)
entry_local = tk.Entry(frame_local, font=("Arial", 10), bd=0, highlightthickness=1, highlightbackground="#555")
entry_local.place(x=30, y=25, relwidth=0.90)
entry_local.insert(0, "C:/Path/To/Your/Video.mp4")

def select_local_file():
    path = filedialog.askopenfilename(
        title="Vyberte .mp4 súbor",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if path:
        entry_local.delete(0, tk.END)
        entry_local.insert(0, path)

btn_select_file = tk.Button(frame_local, text="Select .mp4 to play", command=select_local_file,
                            bg="#FFA500", fg="white", width=14)
btn_select_file.place(x=200)


# Funkcia na aktualizáciu stavu polí podľa výberu
def update_entries():
    if source_var.get() == "youtube":
        entry_youtube.config(state="normal")
        entry_local.config(state="disabled")
    else:
        entry_youtube.config(state="disabled")
        entry_local.config(state="normal")

# Spusti pri štarte a pri zmene
source_var.trace("w", lambda *args: update_entries())
update_entries()

# Ovládacie tlačidlá
frame_controls = tk.Frame(root, bg="#000000", bd=1)
frame_controls.place(relx=0.5, y=280, anchor="center")

btn_start = tk.Button(frame_controls, text="▶️ Spustiť", command=start_wallpaper, bg="#4CAF50", fg="white", width=10)
btn_start.pack(side="left", padx=5)

btn_stop = tk.Button(frame_controls, text="⏹️ Zastaviť", command=stop_wallpaper, bg="#f44336", fg="white", width=10, state="disabled")
btn_stop.pack(side="left", padx=5)

# Stav
label_status = tk.Label(root, text="⏹️ Zastavené", font=("Arial", 10), fg="lightgray", bg="#000000")
label_status.place(relx=0.5, y=330, anchor="center")

# Minimalizovať
btn_minimize = tk.Button(root, text="🗕 Minimize", command=minimize_to_tray, bg="#2196F3", fg="white", width=15)
btn_minimize.place(relx=0.5, y=370, anchor="center")

# Tip
tip_label = tk.Label(root, text="💡 Tip: Try loop videos (example. 'rain loop 4K')", fg="gray", bg="#000000", font=("Arial", 9))
tip_label.place(relx=0.5, y=410, anchor="center")

# Protokol
root.protocol("WM_DELETE_WINDOW", on_closing)

# Spustenie
root.mainloop()
