import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, filedialog  # Добавил filedialog для выбора папки
from threading import Thread
import webbrowser
import zipfile
from urllib.request import urlretrieve
import shutil  # Для удаления директории
import customtkinter as ctk  # Импортируем после установки

def install_yt_dlp():
    try:
        import yt_dlp
        return True
    except ImportError:
        try:
            print("Installing yt-dlp...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-U", "yt-dlp"])
            import yt_dlp
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install yt-dlp: {e}\nPlease install manually: python -m pip install --user -U yt-dlp")
            return False

def install_customtkinter():
    try:
        import customtkinter
        return True
    except ImportError:
        try:
            print("Installing customtkinter...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
            import customtkinter
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install customtkinter: {e}\nPlease install manually: python -m pip install customtkinter")
            return False

def reporthook(count, block_size, total_size):
    # Функция для обновления прогресс-бара при скачивании
    global progress_bar
    progress = count * block_size / total_size
    progress_bar.set(progress)
    progress_window.update_idletasks()

def check_ffmpeg_installed():
    try:
        subprocess.check_output(["ffmpeg", "-version"])
        return True
    except FileNotFoundError:
        if sys.platform.startswith('win'):  # Только для Windows
            global progress_window, progress_bar
            try:
                print("FFmpeg not found in PATH. Checking local installation...")
                
                # Определяем пользовательский путь в AppData\Roaming\ffmpeg
                appdata = os.getenv('APPDATA')
                if not appdata:
                    raise Exception("APPDATA environment variable not found.")
                ffmpeg_dir = os.path.join(appdata, 'ffmpeg')
                
                # Если директория существует, пытаемся добавить путь и проверить
                if os.path.exists(ffmpeg_dir):
                    print("Local FFmpeg directory found. Adding to PATH and verifying...")
                    # Находим папку bin
                    bin_path = None
                    for root, dirs, files in os.walk(ffmpeg_dir):
                        if 'bin' in dirs:
                            bin_path = os.path.join(root, 'bin')
                            break
                    if bin_path:
                        # Добавляем в PATH текущего процесса
                        current_path = os.environ.get('PATH', '')
                        if bin_path not in current_path:
                            os.environ['PATH'] = current_path + os.pathsep + bin_path
                        # Проверяем заново
                        try:
                            subprocess.check_output(["ffmpeg", "-version"])
                            print("Local FFmpeg verified successfully.")
                            return True
                        except FileNotFoundError:
                            print("Local FFmpeg is corrupted or invalid. Reinstalling...")
                    else:
                        print("Bin directory not found in local FFmpeg. Reinstalling...")
                
                # Если не сработало или директории нет — полная установка
                print("Installing FFmpeg...")
                
                # Создаём временное окно с прогресс-баром
                progress_window = ctk.CTk()
                progress_window.title("Installing FFmpeg")
                progress_window.geometry("300x100")
                progress_window.configure(fg_color='#1E1E1E')
                
                label = ctk.CTkLabel(progress_window, text="Downloading and installing FFmpeg...", fg_color='#1E1E1E', text_color='#E0E0E0')
                label.pack(pady=10)
                
                progress_bar = ctk.CTkProgressBar(progress_window, width=250)
                progress_bar.set(0)
                progress_bar.pack(pady=10)
                
                progress_window.update()  # Обновляем окно
                
                # Удаляем существующую директорию, если она есть
                if os.path.exists(ffmpeg_dir):
                    shutil.rmtree(ffmpeg_dir, ignore_errors=True)
                
                # Скачиваем ZIP с прогрессом
                zip_url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
                zip_path = os.path.join(os.getenv('TEMP'), 'ffmpeg.zip')
                urlretrieve(zip_url, zip_path, reporthook=reporthook)
                
                # Распаковываем
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(ffmpeg_dir)
                
                # Находим папку bin заново
                bin_path = None
                for root, dirs, files in os.walk(ffmpeg_dir):
                    if 'bin' in dirs:
                        bin_path = os.path.join(root, 'bin')
                        break
                if not bin_path:
                    raise Exception("Failed to find bin directory after extraction.")
                
                # Добавляем в PATH текущего пользователя (persistent)
                current_path = os.environ.get('PATH', '')
                if bin_path not in current_path:
                    new_path = current_path + os.pathsep + bin_path
                    subprocess.check_call(['setx', 'PATH', new_path])
                
                # Обновляем PATH в текущем процессе
                os.environ['PATH'] = new_path
                
                # Проверяем заново
                subprocess.check_output(["ffmpeg", "-version"])
                
                # Закрываем окно прогресса
                progress_window.destroy()
                
                messagebox.showinfo("Success", "FFmpeg installed successfully!")
                return True
            except Exception as e:
                if 'progress_window' in globals():
                    progress_window.destroy()
                messagebox.showerror("Error", f"Failed to install FFmpeg automatically: {e}\nPlease download from https://ffmpeg.org/download.html and add to PATH manually.")
                return False
        else:
            # Для других ОС — оригинальное предупреждение
            messagebox.showwarning("Warning", "FFmpeg is required for merging video and audio in high resolutions.\nPlease download from https://ffmpeg.org/download.html and add to PATH.")
            return False

def download_video(url, format_str, suffix, dir_path=None):
    if not url:
        messagebox.showerror("Error", "Please enter a URL.")
        return
    try:
        from yt_dlp import YoutubeDL
        outtmpl = f'%(title)s{suffix}.%(ext)s'
        if dir_path:  # Если папка выбрана, добавляем путь
            outtmpl = os.path.join(dir_path, outtmpl)
        ydl_opts = {
            'format': format_str,
            'merge_output_format': 'mp4',
            'outtmpl': outtmpl,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        messagebox.showinfo("Success", "Download complete.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}\nCheck if FFmpeg is installed if needed.")

def start_download(format_str, suffix):
    url = url_entry.get().strip()
    if not url:
        return  # Если URL пустой, ничего не делаем
    # Выбор папки для сохранения
    selected_dir = filedialog.askdirectory(title="Выберите папку для сохранения видео")
    if selected_dir:  # Если выбрана
        thread = Thread(target=download_video, args=(url, format_str, suffix, selected_dir))
        thread.start()
    else:
        messagebox.showinfo("Info", "Скачивание отменено.")

def open_link(event):
    webbrowser.open("https://t.me/nikitasakhnov")

if __name__ == "__main__":
    if not install_yt_dlp():
        sys.exit(1)
    if not install_customtkinter():
        sys.exit(1)
    ctk.set_appearance_mode("Dark")  # Устанавливаем тему заранее
    if not check_ffmpeg_installed():
        # sys.exit(1)  # Раскомментируй, если хочешь остановить скрипт без FFmpeg
        pass
    root = ctk.CTk()
    root.title("🎥 YT Downloader")
    root.geometry("400x300")
    root.configure(fg_color='#1E1E1E')
    label = ctk.CTkLabel(root, text="🔗 Link to the video", fg_color='#1E1E1E', text_color='#E0E0E0', font=ctk.CTkFont(family='Helvetica', size=12))
    label.pack(pady=10)
    url_entry = ctk.CTkEntry(root, width=300, placeholder_text="🔗 Insert the link to YouTube", font=ctk.CTkFont(family='Helvetica', size=12), fg_color='#2A2A2A', text_color='white', border_color='#2A2A2A')
    url_entry.pack()
    button_font = ctk.CTkFont(family='Helvetica', size=12, weight='bold')
    button_width = 200
    button_height = 40
    btn_4k = ctk.CTkButton(root, text="🔥4K", command=lambda: start_download("bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]", "_4k"),
                           fg_color='#E53935', hover_color='#D32F2F', font=button_font, width=button_width, height=button_height)
    btn_4k.pack(pady=5)
    btn_2k = ctk.CTkButton(root, text="🎬 2K", command=lambda: start_download("bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]", "_2k"),
                           fg_color='#FB8C00', hover_color='#EF6C00', font=button_font, width=button_width, height=button_height)
    btn_2k.pack(pady=5)
    btn_1080p = ctk.CTkButton(root, text="📺 1080p", command=lambda: start_download("bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]", "_1080p"),
                              fg_color='#43A047', hover_color='#388E3C', font=button_font, width=button_width, height=button_height)
    btn_1080p.pack(pady=5)
    footer_frame = ctk.CTkFrame(root, fg_color='#1E1E1E')
    footer_frame.pack(side='bottom', fill='x', pady=10)
    footer = ctk.CTkLabel(footer_frame, text="Made by NikS", fg_color='#1E1E1E', text_color='#E0E0E0', font=ctk.CTkFont(family='Helvetica', size=12, weight='bold'))
    footer.pack(side='left', padx=10)
    link = ctk.CTkLabel(footer_frame, text="Telegram channel 👈", fg_color='#1E1E1E', text_color='#3498DB', font=ctk.CTkFont(family='Helvetica', size=12, weight='bold'), cursor="hand2")
    link.pack(side='left')
    link.bind("<Button-1>", open_link)
    root.mainloop()