import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import yt_dlp
import re
import threading

def extraer_urls(texto):
    patron = r'(https?://(?:www\.youtube\.com/watch\?v=[\w\-]+|youtu\.be/[\w\-]+))'
    return re.findall(patron, texto)

def convertir_youtu_be(url):
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def inicializar_urls_textbox(urls):
    urls_status_text.config(state='normal')
    urls_status_text.delete("1.0", tk.END)
    for url in urls:
        urls_status_text.insert(tk.END, f"{url} (Pendiente)\n")
    urls_status_text.config(state='disabled')

def actualizar_estado_url_en_textbox(url, estado):
    urls_status_text.config(state='normal')
    lineas = urls_status_text.get("1.0", tk.END).splitlines()
    for idx, linea in enumerate(lineas):
        if url in linea:
            # Reemplazar el estado entre paréntesis (si existe) por el nuevo estado
            nueva_linea = re.sub(r"\(.*\)", f"({estado})", linea)
            if nueva_linea == linea:
                # Si no tenía estado, lo añadimos
                nueva_linea = f"{linea} ({estado})"
            lineas[idx] = nueva_linea
            break
    # Volver a escribir el contenido actualizado
    urls_status_text.delete("1.0", tk.END)
    urls_status_text.insert(tk.END, "\n".join(lineas) + "\n")
    urls_status_text.config(state='disabled')

def descargar_videos_en_thread(urls):
    total = len(urls)
    descargados = 0
    errores = 0

    for idx, url in enumerate(urls):
        try:
            ydl_opts = {}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            descargados += 1
            actualizar_estado_url_en_textbox(url, "Descargado")
        except Exception:
            errores += 1
            actualizar_estado_url_en_textbox(url, "Error")
        # Actualizar barra y estado
        progress['value'] = descargados + errores
        status_label.config(text=f"Descargados: {descargados}/{total} | Errores: {errores}")
        root.update_idletasks()

    messagebox.showinfo("Descarga completa", f"Descargados: {descargados} de {total} vídeos.\nErrores: {errores}")

def descargar_videos():
    texto = url_text.get("1.0", tk.END)
    urls = extraer_urls(texto)
    urls = [convertir_youtu_be(u) for u in urls]
    total = len(urls)
    if total == 0:
        messagebox.showwarning("Sin URLs", "No se encontraron URLs de YouTube válidas.")
        return
    progress['maximum'] = total
    progress['value'] = 0
    status_label.config(text=f"Descargados: 0/{total} | Errores: 0")
    inicializar_urls_textbox(urls)
    hilo = threading.Thread(target=descargar_videos_en_thread, args=(urls,), daemon=True)
    hilo.start()

# Interfaz gráfica
root = tk.Tk()
root.title("Descargador de YouTube (múltiples vídeos)")

url_label = tk.Label(root, text="Pega aquí el texto con las URLs de YouTube:")
url_label.pack(pady=10)

url_text = scrolledtext.ScrolledText(root, width=60, height=6)
url_text.pack(pady=5)

download_button = tk.Button(root, text="Descargar Vídeos", command=descargar_videos)
download_button.pack(pady=10)

progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.pack(pady=5)

status_label = tk.Label(root, text="Descargados: 0/0 | Errores: 0")
status_label.pack(pady=5)

urls_status_label = tk.Label(root, text="Estado de cada URL:")
urls_status_label.pack(pady=(10,0))

urls_status_text = scrolledtext.ScrolledText(root, width=60, height=10, state='disabled')
urls_status_text.pack(pady=5)

root.mainloop()
