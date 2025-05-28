import requests
import tempfile
import tkinter as tk
import re
import threading
import sys
import os
import tkinter.scrolledtext as st
import queue
from tkinter import ttk, messagebox
from pytubefix import YouTube
from pytubefix.cli import on_progress
from PIL import ImageTk, Image, ImageSequence
from io import BytesIO
from moviepy.editor import VideoFileClip, AudioFileClip

q = queue.Queue()

class ConsoleTee:
    def __init__(self, original, queue):
        #self.original = original
        self.queue = queue

    def write(self, msg):
        # self.original.write(msg)
        self.queue.put(msg)

    def flush(self):
        #self.original.flush()
        pass

def console_update_worker():
    buffer = []
    while True:
        msg = q.get()
        buffer.append(msg)
        while not q.empty():
            buffer.append(q.get_nowait())

        def append_text():
            console_output.configure(state='normal')
            console_output.insert(tk.END, ''.join(buffer))
            console_output.see(tk.END)
            console_output.configure(state='disabled')

        root.after(0, append_text)
        buffer.clear()

def download_thread():
    threading.Thread(target=download, daemon=True).start()

def download():
    def animate(i=0):
        if running:
            resized_frame = frames_resized[i]
            loadgif.config(image=resized_frame)
            root.after(30, animate, (i + 1) % len(frames_resized))

    global running
    running = True

    def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    gif_path = resource_path("amongus.gif")
    gif = Image.open(gif_path)
    frames_resized = [ImageTk.PhotoImage(f.copy().resize((95, 100))) for f in ImageSequence.Iterator(gif)]
    global loadgif
    loadgif = tk.Label(root, bg='grey20')
    loadgif.grid(row=0, column=4, rowspan=2)
    animate()

    url = entry.get()
    resl = resolution.get()
    if resl == " ":
        messagebox.showerror("Error", "Select a resolution after checking the available resolutions")
    elif resl == "mp3":
        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            audio = yt.streams.filter(only_audio=True, file_extension="mp4").first()
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as audio_temp:
                audio.stream_to_buffer(audio_temp)
                audio_temp.flush()
                audio_clip = AudioFileClip(audio_temp.name)
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', yt.title)
                audio_clip.write_audiofile(f"{safe_title}-audio-only.mp3")
                audio_clip.close()
        except Exception as e:
            print(e)
            messagebox.showerror("Error", "Unable to Fetch. Does it even Exist?")
    elif resl in res and resl in res_m:
        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            ys = yt.streams.filter(res=resl, progressive=True, file_extension="mp4").first()
            ys.download()
        except Exception as e:
            print(e)
            messagebox.showerror("Error", "An error occurred while downloading the video")
    else:
        try:
            yt = YouTube(url, on_progress_callback=on_progress)
            video_stream = yt.streams.filter(adaptive=True, only_video=True, file_extension="mp4", resolution=resl).first()
            audio_stream = yt.streams.filter(only_audio=True, file_extension="mp4").first()
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as video_temp, \
                    tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as audio_temp:

                video_stream.stream_to_buffer(video_temp)
                audio_stream.stream_to_buffer(audio_temp)

                video_temp.flush()
                audio_temp.flush()

                video = VideoFileClip(video_temp.name)
                audio = AudioFileClip(audio_temp.name)
                final = video.set_audio(audio)

                fl_name = re.sub(r'[<>:"/\\|?*]', '_', yt.title)
                final.write_videofile(f"{fl_name}-{resl}.mp4", codec="libx264", audio_codec="aac")
        except Exception as e:
            print(e)
            messagebox.showerror("Error", "An error occurred while downloading the video")
    running = False
    loadgif.grid_forget()
    messagebox.showinfo(title="Completed", message="Your file has been successfully downloaded!")

def check_res():
    global res, thumbnail, img, res_m
    url = entry.get()
    try:
        yt = YouTube(url)
        res = []
        res_m = []

        for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
            if stream.resolution not in res:
                res.append(stream.resolution)
                res_m.append(stream.resolution)
            print(f"Progressive: {stream.resolution} - {stream.mime_type}")

        for stream in yt.streams.filter(adaptive=True, only_video=True):
            if stream.resolution not in res:
                res.append(stream.resolution)
            print(f"Adaptive: {stream.resolution} - {stream.mime_type}")
        res.append("mp3")
        resolution['values'] = res
        resolution.current(0)

        thumb_url = f"https://img.youtube.com/vi/{yt.video_id}/default.jpg"
        img_data = requests.get(thumb_url).content

        img = ImageTk.PhotoImage(Image.open(BytesIO(img_data)))

        if 'thumbnail' in globals():
            thumbnail.config(image=img)
            thumbnail.image = img
        else:
            thumbnail = tk.Label(root, image=img, bg='grey20')
            thumbnail.image = img
            thumbnail.grid(row=0, column=3, rowspan=2)
    except Exception as e:
        if str(e) == "regex_search: could not find match for (?:v=|\/)([0-9A-Za-z_-]{11}).*":
            messagebox.showerror("Error", "Enter a valid URL")
        else:
            print(e)
            messagebox.showerror("Error", str(e))


running = False
res = [" "]
res_m = []

button_style = {
    "bg": "#333333",
    "fg": "white",
    "activebackground": "#444444",
    "activeforeground": "white",
    "borderwidth": 2,
    "relief": "raised"
}

entry_style = {
    "bg": "grey20",
    "fg": "white",
    "insertbackground": "white",
    "highlightbackground": "white",
    "highlightcolor": "white",
    "highlightthickness": 2,
    "relief": "flat"
}

label_style = {
    "bg": "grey20",
    "fg": "white"
}

combo_style = {
    "background": "#333333",
    "fieldbackground": "grey20",
    "foreground": "white"
}

root = tk.Tk()
root.title("AYTD - YouTube Downloader")
root.geometry("800x220")
root.configure(bg='grey20')

label = tk.Label(root, text="Enter URL:", **label_style)
label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

entry = tk.Entry(root, width=30, **entry_style)
entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

check_button = tk.Button(root, text="Check", **button_style, command=check_res)
check_button.grid(row=0, column=2, sticky="w", padx=10, pady=5)

label2 = tk.Label(root, text="Resolution:", **label_style)
label2.grid(row=1, column=0, columnspan=3, sticky="w", padx=10, pady=5)

style = ttk.Style()
style.theme_use('clam')
style.configure("TCombobox",
                fieldbackground="grey20",
                background="#333333",
                foreground="white")

resolution = ttk.Combobox(root, values=res, style="TCombobox")
resolution.current(0)
resolution.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

download_button = tk.Button(root, text="Download", **button_style, command=download_thread)
download_button.grid(row=1, column=2, sticky="w", padx=10, pady=10)

console_output = st.ScrolledText(root, height=7, state='disabled', bg='grey20', fg='white', insertbackground='white')
console_output.grid(row=3, column=0, columnspan=5, sticky="nsew", padx=10, pady=5)

root.grid_rowconfigure(4, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(3, minsize=170)
root.grid_columnconfigure(4, minsize=120)

original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = ConsoleTee(original_stdout, q)
sys.stderr = ConsoleTee(original_stderr, q)
threading.Thread(target=console_update_worker, daemon=True).start()

root.mainloop()
