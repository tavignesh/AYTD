import tkinter as tk
from tkinter import ttk, messagebox
from pytubefix import YouTube
from pytubefix.cli import on_progress
from PIL import ImageTk, Image, ImageSequence
import requests
from io import BytesIO
import tempfile
from moviepy.editor import VideoFileClip, AudioFileClip
import re
import threading
import sys
import tkinter.scrolledtext as st
import queue

#https://www.youtube.com/watch?v=rJNBGqiBI7s
q = queue.Queue()

class ConsoleTee:
    def __init__(self, original, queue):
        self.original = original
        self.queue = queue

    def write(self, msg):
        self.original.write(msg)
        self.queue.put(msg)

    def flush(self):
        self.original.flush()

def console_update_worker():
    buffer = []
    while True:
        msg = q.get()  # Blocking wait for new message
        buffer.append(msg)
        # Collect all currently available messages
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
            loadgif.config(image=frames[i])
            root.after(30, animate, (i + 1) % len(frames))

    global running
    running = True

    gif = Image.open("amongus.gif")
    frames = [ImageTk.PhotoImage(f.copy()) for f in ImageSequence.Iterator(gif)]
    global loadgif
    loadgif = tk.Label(root)
    loadgif.pack()
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
    loadgif.pack_forget()

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
            thumbnail = tk.Label(root, image=img)
            thumbnail.image = img
            thumbnail.pack()
    except Exception as e:
        if str(e) == "regex_search: could not find match for (?:v=|\/)([0-9A-Za-z_-]{11}).*":
                messagebox.showerror("Error", "Enter a valid URL")
        else:
            messagebox.showerror("Error", str(e))

# Initialize globals
running = False
res = [" "]
res_m = []

# Setup Tkinter window
root = tk.Tk()
root.title("AYTD - YouTube Downloader")
root.geometry("300x600")

label = tk.Label(root, text="Enter URL")
label.pack(pady=10)

entry = tk.Entry(root, width=30)
entry.pack(pady=5)

resolution = ttk.Combobox(root, values=res)
resolution.current(0)
resolution.pack(pady=5)

check_button = tk.Button(root, text="Check", command=check_res)
check_button.pack(pady=10)

download_button = tk.Button(root, text="Download", command=download_thread)
download_button.pack(pady=10)

console_output = st.ScrolledText(root, height=10, state='disabled')
console_output.pack(fill='both', expand=True)

original_stdout = sys.stdout
original_stderr = sys.stderr

sys.stdout = ConsoleTee(original_stdout, q)
sys.stderr = ConsoleTee(original_stderr, q)

# Start console update thread
threading.Thread(target=console_update_worker, daemon=True).start()

root.mainloop()
