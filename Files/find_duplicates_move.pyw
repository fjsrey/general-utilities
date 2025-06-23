# pip install pillow
import os
import hashlib
import shutil
import argparse
import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image
from PIL.ExifTags import TAGS

def calcular_md5(archivo):
    hasher = hashlib.md5()
    with open(archivo, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def obtener_fecha_exif(ruta):
    try:
        with Image.open(ruta) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == "DateTimeOriginal":
                        return value.replace(':', '-', 2).replace(':', '-')  # Formato AAAA-MM-DD HH-MM
    except Exception:
        pass
    return None


def encontrar_duplicados(carpeta_origen):
    archivos = []
    for root, _, files in os.walk(carpeta_origen):
        for file in files:
            ruta_completa = os.path.join(root, file)
            if os.path.getsize(ruta_completa) == 0:  # Si el archivo ocupa 0 bytes
                os.remove(ruta_completa)  # Eliminar el archivo
                log_callback(f"Eliminando fichero sin contenido: {ruta_completa}\n")
                continue  # No agregarlo al array

            fecha_exif = obtener_fecha_exif(ruta_completa)
            if fecha_exif:
                nombre_base, extension = os.path.splitext(file)
                nuevo_nombre = f"{nombre_base}_{fecha_exif}{extension}"
                nueva_ruta = os.path.join(root, nuevo_nombre)
                os.rename(ruta_completa, nueva_ruta)
                ruta_completa = nueva_ruta
                file = nuevo_nombre

            md5 = calcular_md5(ruta_completa)
            archivos.append([ruta_completa, file, md5])
    return archivos


def mover_duplicados(archivos, carpeta_destino, log_callback):
    hash_dict = {}
    for archivo in archivos:
        ruta, nombre, md5 = archivo
        if md5 not in hash_dict:
            hash_dict[md5] = [archivo]
        else:
            hash_dict[md5].append(archivo)
    
    archivos_duplicados = [group for group in hash_dict.values() if len(group) > 1]
    archivos_duplicados.sort(key=lambda x: x[0][2])
    
    contador_dict = {}
    for grupo in archivos_duplicados:
        primero = True
        original = grupo[0][0]
        for ruta, nombre, md5 in grupo:
            if primero:
                primero = False
                continue
            contador = contador_dict.get(md5, 1)
            nombre_base, extension = os.path.splitext(nombre)
            nuevo_nombre = f"{nombre_base}_{contador}{extension}"
            contador_dict[md5] = contador + 1
            nueva_ruta = os.path.join(carpeta_destino, nuevo_nombre)
            
            if os.path.dirname(ruta) != carpeta_destino:
                shutil.move(ruta, nueva_ruta)
                log_callback(f"Movido: {ruta} -> {nueva_ruta}\n")
                log_callback(f"Duplicado de: {original}\n")


def ordenar_por_extension(carpeta_origen, log_callback):
    for root, _, files in os.walk(carpeta_origen):
        for file in files:
            ruta_completa = os.path.join(root, file)
            _, extension = os.path.splitext(file)
            if extension:
                carpeta_extension = os.path.join(carpeta_origen, extension[1:].upper())
                if not os.path.exists(carpeta_extension):
                    os.makedirs(carpeta_extension)
                
                nueva_ruta = os.path.join(carpeta_extension, file)
                contador = 1
                while os.path.exists(nueva_ruta):
                    nombre_base, ext = os.path.splitext(file)
                    nuevo_nombre = f"{nombre_base}_{contador}{ext}"
                    nueva_ruta = os.path.join(carpeta_extension, nuevo_nombre)
                    contador += 1
                
                shutil.move(ruta_completa, nueva_ruta)
                log_callback(f"Movido: {ruta_completa} -> {nueva_ruta}\n")

def borrar_carpetas_vacias(carpeta_origen, log_callback):
    for root, dirs, _ in os.walk(carpeta_origen, topdown=False):
        for dir in dirs:
            carpeta = os.path.join(root, dir)
            if not os.listdir(carpeta):
                os.rmdir(carpeta)
                log_callback(f"Carpeta eliminada: {carpeta}\n")

def ejecutar(carpeta_origen, carpeta_destino, ordenar, borrar_vacias, log_callback):
    log_callback(f"Escaneando {carpeta_origen}...\n")
    archivos = encontrar_duplicados(carpeta_origen)
    log_callback(f"Se encontraron {len(archivos)} archivos.\n")
    mover_duplicados(archivos, carpeta_destino, log_callback)
    if ordenar:
        log_callback("Ordenando ficheros por extensión...\n")
        ordenar_por_extension(carpeta_origen, log_callback)
    if borrar_vacias:
        log_callback("Eliminando carpetas vacías...\n")
        borrar_carpetas_vacias(carpeta_origen, log_callback)
    log_callback("Proceso completado.\n")

def interfaz_grafica():
    def seleccionar_carpeta_origen():
        entrada_origen.set(filedialog.askdirectory())
    
    def seleccionar_carpeta_destino():
        entrada_destino.set(filedialog.askdirectory())
    
    def log_callback(mensaje):
        log_text.insert(tk.END, mensaje)
        log_text.yview(tk.END)
        root.update_idletasks()
    
    def iniciar_proceso():
        origen = entrada_origen.get()
        destino = entrada_destino.get()
        if origen and destino:
            ejecutar(origen, destino, ordenar_var.get(), borrar_vacias_var.get(), log_callback)
    
    root = tk.Tk()
    root.title("Detector de Archivos Duplicados")
    root.geometry("800x550")
    root.columnconfigure(1, weight=1)
    root.rowconfigure(3, weight=1)
    
    tk.Label(root, text="Carpeta Origen:").grid(row=0, column=0, sticky='w')
    entrada_origen = tk.StringVar()
    tk.Entry(root, textvariable=entrada_origen, width=50).grid(row=0, column=1, sticky='ew')
    tk.Button(root, text="Seleccionar", command=seleccionar_carpeta_origen).grid(row=0, column=2)
    
    tk.Label(root, text="Carpeta Destino:").grid(row=1, column=0, sticky='w')
    entrada_destino = tk.StringVar()
    tk.Entry(root, textvariable=entrada_destino, width=50).grid(row=1, column=1, sticky='ew')
    tk.Button(root, text="Seleccionar", command=seleccionar_carpeta_destino).grid(row=1, column=2)
    
    ordenar_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Ordenar ficheros al finalizar", variable=ordenar_var).grid(row=2, column=1, sticky='w')
    
    borrar_vacias_var = tk.BooleanVar()
    tk.Checkbutton(root, text="Borrar carpetas vacías", variable=borrar_vacias_var).grid(row=3, column=1, sticky='w')
    
    tk.Button(root, text="Iniciar", command=iniciar_proceso).grid(row=4, column=1)
    
    log_text = scrolledtext.ScrolledText(root, width=80, height=20)
    log_text.grid(row=5, column=0, columnspan=3, sticky='nsew')
    
    root.mainloop()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--origen", help="Carpeta de origen")
    parser.add_argument("--destino", help="Carpeta de destino")
    parser.add_argument("--ordenar", action="store_true", help="Ordenar ficheros por extensión al finalizar")
    parser.add_argument("--borrar_vacias", action="store_true", help="Borrar carpetas vacías")
    args = parser.parse_args()
    
    if args.origen and args.destino:
        def print_log(msg):
            print(msg, end="")
        ejecutar(args.origen, args.destino, args.ordenar, args.borrar_vacias, print_log)
    else:
        interfaz_grafica()

if __name__ == "__main__":
    main()
