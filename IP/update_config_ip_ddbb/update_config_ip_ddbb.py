"""
Actualizador de IP en archivos con interfaz gráfica.

FUNCIONALIDAD:
- Permite seleccionar una IP de las interfaces del equipo (incluyendo siempre 127.0.0.1).
- Permite gestionar (añadir, modificar, eliminar) la lista de archivos a modificar, almacenada en el fichero de configuración 'update_config_ip_ddbb.config'.
- Permite modificar el patrón de la expresión regular usado para buscar y reemplazar en los archivos, también guardado en la configuración.
- Al pulsar "Actualizar archivos", reemplaza todas las coincidencias del patrón por la IP seleccionada en todos los archivos de la lista.
- El botón "Salir" permite cerrar la aplicación (no se cierra automáticamente tras actualizar).
- El botón "Actualizar archivos" solo está activo si hay archivos en la lista.
- El patrón de la expresión regular puede editarse desde la interfaz gráfica.
- Si el patrón no está en la configuración, se usa el patrón por defecto para IPs IPv4.
- Todos los errores y eventos importantes se registran en un archivo de log.

FORMATO DEL FICHERO DE CONFIGURACIÓN (update_config_ip_ddbb.config):
- Cada línea con la ruta de un archivo a modificar.
- Una línea especial: pattern=... para el patrón de la expresión regular.
  Ejemplo:
    C:\ruta\archivo1.txt
    C:\ruta\archivo2.txt
    pattern=\b(?:\d{1,3}\.){3}\d{1,3}\b

REQUISITOS:
- Python 3.x
- No requiere librerías externas, salvo tkinter, solo las estándar.
- Para instalar tkinter, ejecutar: pip install tkinter

AUTOR: Perplexity AI, bajo supervisión de Francisco José Serrano Rey
"""

import socket
import re
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import os
import logging
import configparser

CONFIG_FILE = "update_config_ip_ddbb.config"
LOG_FILE = "update_config_ip_ddbb.log"
DEFAULT_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log_event(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)

def obtener_ips_interfaces():
    ips = set()
    hostname = socket.gethostname()
    try:
        for resultado in socket.getaddrinfo(hostname, None):
            ip = resultado[4][0]
            if '.' in ip:
                ips.add(ip)
    except Exception as e:
        log_error(f"Error obteniendo IPs de interfaces: {e}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        ips.add(ip)
        s.close()
    except Exception as e:
        log_error(f"Error obteniendo IP principal: {e}")
    ips.add("127.0.0.1")
    return sorted(list(ips), key=lambda x: [int(part) for part in x.split('.')])

def reemplazar_ip_en_fichero(ruta_fichero, nueva_ip, patron_regex):
    try:
        with open(ruta_fichero, 'r', encoding='utf-8') as f:
            contenido = f.read()
        nuevo_contenido = re.sub(patron_regex, nueva_ip, contenido)
        with open(ruta_fichero, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        log_event(f"Actualizado: {ruta_fichero} (patrón: {patron_regex}, nueva IP: {nueva_ip})")
    except Exception as e:
        log_error(f"No se pudo modificar el archivo {ruta_fichero}: {e}")
        messagebox.showerror("Error", f"No se pudo modificar el archivo:\n{ruta_fichero}\n\n{e}")

def cargar_configuracion():
    archivos = []
    patron = None
    ips_personalizadas = {}
    patrones = {}
    patron_seleccionado = None

    if os.path.exists(CONFIG_FILE):
        try:
            config = configparser.ConfigParser(strict=False)
            config.read(CONFIG_FILE, encoding="utf-8")

            if 'personalizadas' in config:
                ips_personalizadas = dict(config['personalizadas'])

            if 'patrones' in config:
                patrones = dict(config['patrones'])

            if 'general' in config:
                if 'pattern' in config['general']:
                    patron = config['general']['pattern']
                if 'pattern_selected' in config['general']:
                    patron_seleccionado = config['general']['pattern_selected']

            if 'archivos' in config:
                archivos = [ruta for clave, ruta in config['archivos'].items()]
        except Exception as e:
            log_error(f"Error al cargar la configuración: {e}")

    if not patrones:
        patrones = {"IPv4": DEFAULT_PATTERN}
    if patron_seleccionado is None:
        patron_seleccionado = next(iter(patrones))
    if patron is None:
        patron = patrones.get(patron_seleccionado, DEFAULT_PATTERN)
        log_event("No se encontró patrón en la configuración. Usando patrón por defecto.")

    return archivos, patron, ips_personalizadas, patrones, patron_seleccionado

def guardar_configuracion(archivos, patron, ips_personalizadas, patrones, patron_seleccionado):
    try:
        config = configparser.ConfigParser()
        config['general'] = {
            'pattern': patron,
            'pattern_selected': patron_seleccionado
        }
        config['archivos'] = {f'archivo{i+1}': ruta for i, ruta in enumerate(archivos)}
        config['personalizadas'] = ips_personalizadas
        config['patrones'] = patrones
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            config.write(f)
        log_event("Configuración guardada correctamente.")
    except Exception as e:
        log_error(f"Error al guardar la configuración: {e}")

def actualizar_archivos(ip_elegida, archivos, patron_regex):
    for archivo in archivos:
        reemplazar_ip_en_fichero(archivo, ip_elegida, patron_regex)
    log_event(f"Actualización completada para la IP {ip_elegida} en los archivos seleccionados.")
    messagebox.showinfo("Actualización completada", f"IPs actualizadas a {ip_elegida} en los ficheros indicados.")

def refrescar_lista_ips():
    lista_ips.delete(0, tk.END)
    for ip in ips_detectadas:
        lista_ips.insert(tk.END, ip)
    for ip, desc in ips_personalizadas.items():
        texto = f"{ip} - {desc}" if desc else ip
        lista_ips.insert(tk.END, texto)

def refrescar_lista_archivos():
    archivos_listbox.delete(0, tk.END)
    for archivo in archivos_lista:
        archivos_listbox.insert(tk.END, archivo)
    actualizar_estado_boton_actualizar()

def on_aceptar():
    seleccion = lista_ips.curselection()
    if not seleccion:
        messagebox.showwarning("Selección requerida", "Debes seleccionar una IP antes de continuar.")
        return
    idx = seleccion[0]
    if idx < len(ips_detectadas):
        ip_elegida = ips_detectadas[idx]
    else:
        ip_elegida = list(ips_personalizadas.keys())[idx - len(ips_detectadas)]
    log_event(f"Botón actualizar pulsado. IP seleccionada: {ip_elegida}")
    actualizar_archivos(ip_elegida, archivos_lista, patron_var.get())

def on_doble_click(event):
    seleccion = lista_ips.curselection()
    if seleccion:
        idx = seleccion[0]
        if idx < len(ips_detectadas):
            ip_elegida = ips_detectadas[idx]
        else:
            ip_elegida = list(ips_personalizadas.keys())[idx - len(ips_detectadas)]
        log_event(f"Doble click en IP: {ip_elegida}")
        actualizar_archivos(ip_elegida, archivos_lista, patron_var.get())

def actualizar_estado_boton_actualizar():
    if archivos_lista:
        btn_actualizar.config(state=tk.NORMAL)
    else:
        btn_actualizar.config(state=tk.DISABLED)

def on_cerrar():
    guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
    log_event("Aplicación cerrada por el usuario.")
    root.destroy()

def gestionar_ips_personalizadas():
    ventana = tk.Toplevel(root)
    ventana.title("Gestionar IPs personalizadas")
    ventana.geometry("600x300")
    ventana.transient(root)
    ventana.grab_set()
    ventana.focus_set()

    lista_personalizadas = tk.Listbox(ventana, font=("Consolas", 14), width=60)
    lista_personalizadas.pack(pady=10, padx=20)

    def refrescar():
        lista_personalizadas.delete(0, tk.END)
        for ip, desc in ips_personalizadas.items():
            lista_personalizadas.insert(tk.END, f"{ip} - {desc}" if desc else ip)
        refrescar_lista_ips()

    def añadir_ip():
        ip = simpledialog.askstring("Nueva IP", "Introduce la IP:", parent=ventana)
        if not ip or ip.strip() in ips_personalizadas:
            messagebox.showerror("Error", "IP inválida o ya existente.", parent=ventana)
            return
        desc = simpledialog.askstring("Descripción", "Introduce la descripción:", parent=ventana)
        ips_personalizadas[ip.strip()] = desc.strip() if desc else ""
        refrescar()
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())

    def modificar_ip():
        seleccion = lista_personalizadas.curselection()
        if not seleccion:
            return
        ip_actual = list(ips_personalizadas.keys())[seleccion[0]]
        desc_actual = ips_personalizadas[ip_actual]
        nueva_ip = simpledialog.askstring("Modificar IP", "Nueva IP:", initialvalue=ip_actual, parent=ventana)
        if not nueva_ip:
            return
        nueva_ip = nueva_ip.strip()
        if nueva_ip != ip_actual and nueva_ip in ips_personalizadas:
            messagebox.showerror("Error", "La IP ya existe.", parent=ventana)
            return
        nueva_desc = simpledialog.askstring("Modificar descripción", "Nueva descripción:", initialvalue=desc_actual, parent=ventana)
        if nueva_desc is None:
            return
        nueva_desc = nueva_desc.strip()
        del ips_personalizadas[ip_actual]
        ips_personalizadas[nueva_ip] = nueva_desc
        refrescar()
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())

    def eliminar_ip():
        seleccion = lista_personalizadas.curselection()
        if not seleccion:
            return
        ip = list(ips_personalizadas.keys())[seleccion[0]]
        if messagebox.askyesno("Confirmar", f"¿Eliminar IP {ip}?", parent=ventana):
            del ips_personalizadas[ip]
            refrescar()
            guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())

    frame = tk.Frame(ventana)
    frame.pack(pady=5)

    tk.Button(frame, text="Añadir", width=12, command=añadir_ip, bg="#5bc0de", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Modificar", width=12, command=modificar_ip, bg="#f0ad4e", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Eliminar", width=12, command=eliminar_ip, bg="#d9534f", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Cerrar", width=12, command=ventana.destroy, bg="#343a40", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)

    refrescar()
    ventana.wait_window()

def gestionar_ficheros():
    ventana = tk.Toplevel(root)
    ventana.title("Gestionar ficheros")
    ventana.geometry("800x350")
    ventana.transient(root)
    ventana.grab_set()
    ventana.focus_set()

    lista_ficheros = tk.Listbox(ventana, font=("Consolas", 13), width=90, height=10)
    lista_ficheros.pack(pady=10, padx=20)

    def refrescar():
        lista_ficheros.delete(0, tk.END)
        for archivo in archivos_lista:
            lista_ficheros.insert(tk.END, archivo)
        refrescar_lista_archivos()

    def añadir_archivo():
        fichero = filedialog.askopenfilename(title="Selecciona un archivo a añadir", parent=ventana)
        if fichero and fichero not in archivos_lista:
            archivos_lista.append(fichero)
            refrescar()
            guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
            log_event(f"Archivo añadido: {fichero}")

    def modificar_archivo():
        seleccion = lista_ficheros.curselection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Selecciona un archivo para modificar.", parent=ventana)
            return
        idx = seleccion[0]
        fichero = filedialog.askopenfilename(title="Selecciona el nuevo archivo", parent=ventana)
        if fichero:
            log_event(f"Archivo modificado: {archivos_lista[idx]} -> {fichero}")
            archivos_lista[idx] = fichero
            refrescar()
            guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())

    def eliminar_archivo():
        seleccion = lista_ficheros.curselection()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Selecciona un archivo para eliminar.", parent=ventana)
            return
        idx = seleccion[0]
        log_event(f"Archivo eliminado: {archivos_lista[idx]}")
        del archivos_lista[idx]
        refrescar()
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())

    frame = tk.Frame(ventana)
    frame.pack(pady=5)

    tk.Button(frame, text="Añadir", width=12, command=añadir_archivo, bg="#5bc0de", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Modificar", width=12, command=modificar_archivo, bg="#f0ad4e", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Eliminar", width=12, command=eliminar_archivo, bg="#d9534f", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Cerrar", width=12, command=ventana.destroy, bg="#343a40", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)

    refrescar()
    ventana.wait_window()

def gestionar_patrones():
    ventana = tk.Toplevel(root)
    ventana.title("Gestionar patrones")
    ventana.geometry("800x350")
    ventana.transient(root)
    ventana.grab_set()
    ventana.focus_set()

    lista_patrones = tk.Listbox(ventana, font=("Consolas", 13), width=90, height=10)
    lista_patrones.pack(pady=10, padx=20)

    def refrescar():
        lista_patrones.delete(0, tk.END)
        for nombre, patron in patrones.items():
            seleccionado = " (seleccionado)" if nombre == patron_seleccionado_var.get() else ""
            lista_patrones.insert(tk.END, f"{nombre}: {patron}{seleccionado}")
        # Actualiza patrón en la interfaz principal
        patron_var.set(patrones[patron_seleccionado_var.get()])

    def seleccionar_patron():
        seleccion = lista_patrones.curselection()
        if not seleccion:
            return
        nombre = list(patrones.keys())[seleccion[0]]
        patron_seleccionado_var.set(nombre)
        patron_var.set(patrones[nombre])
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
        refrescar()

    def añadir_patron():
        nombre = simpledialog.askstring("Nombre del patrón", "Introduce un nombre para el patrón:", parent=ventana)
        if not nombre or nombre.strip() in patrones:
            messagebox.showerror("Error", "Nombre inválido o ya existente.", parent=ventana)
            return
        patron = simpledialog.askstring("Patrón", "Introduce el patrón (expresión regular):", parent=ventana)
        if not patron:
            return
        patrones[nombre.strip()] = patron.strip()
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
        refrescar()

    def modificar_patron():
        seleccion = lista_patrones.curselection()
        if not seleccion:
            return
        nombre_actual = list(patrones.keys())[seleccion[0]]
        patron_actual = patrones[nombre_actual]
        nuevo_nombre = simpledialog.askstring("Modificar nombre", "Nuevo nombre:", initialvalue=nombre_actual, parent=ventana)
        if not nuevo_nombre:
            return
        nuevo_nombre = nuevo_nombre.strip()
        if nuevo_nombre != nombre_actual and nuevo_nombre in patrones:
            messagebox.showerror("Error", "El nombre ya existe.", parent=ventana)
            return
        nuevo_patron = simpledialog.askstring("Modificar patrón", "Nuevo patrón:", initialvalue=patron_actual, parent=ventana)
        if not nuevo_patron:
            return
        # Actualiza el diccionario
        del patrones[nombre_actual]
        patrones[nuevo_nombre] = nuevo_patron.strip()
        # Si era el seleccionado, actualiza el seleccionado
        if patron_seleccionado_var.get() == nombre_actual:
            patron_seleccionado_var.set(nuevo_nombre)
            patron_var.set(nuevo_patron.strip())
        guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
        refrescar()

    def eliminar_patron():
        seleccion = lista_patrones.curselection()
        if not seleccion:
            return
        nombre = list(patrones.keys())[seleccion[0]]
        if len(patrones) == 1:
            messagebox.showerror("Error", "Debe haber al menos un patrón.", parent=ventana)
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el patrón '{nombre}'?", parent=ventana):
            del patrones[nombre]
            # Si era el seleccionado, selecciona el primero
            if patron_seleccionado_var.get() == nombre:
                patron_seleccionado_var.set(next(iter(patrones)))
                patron_var.set(patrones[patron_seleccionado_var.get()])
            guardar_configuracion(archivos_lista, patron_var.get(), ips_personalizadas, patrones, patron_seleccionado_var.get())
            refrescar()

    frame = tk.Frame(ventana)
    frame.pack(pady=5)

    tk.Button(frame, text="Seleccionar", width=12, command=seleccionar_patron, bg="#0275d8", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Añadir", width=12, command=añadir_patron, bg="#5bc0de", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Modificar", width=12, command=modificar_patron, bg="#f0ad4e", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Eliminar", width=12, command=eliminar_patron, bg="#d9534f", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Cerrar", width=12, command=ventana.destroy, bg="#343a40", fg="white", font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=5)

    refrescar()
    ventana.wait_window()

# Interfaz gráfica
root = tk.Tk()
root.title("Actualizador de IP en archivos")
root.geometry("1100x800")
root.resizable(False, False)

fuente_grande = ("Arial", 20)
fuente_lista = ("Consolas", 20)
fuente_boton = ("Arial", 16, "bold")
fuente_archivos = ("Consolas", 15)
fuente_patron = ("Consolas", 15)

tk.Label(root, text="Selecciona la IP a utilizar:", font=fuente_grande).pack(pady=12)

archivos_lista, patron_guardado, ips_personalizadas, patrones, patron_seleccionado = cargar_configuracion()
ips_detectadas = obtener_ips_interfaces()

patron_var = tk.StringVar(value=patron_guardado)
patron_seleccionado_var = tk.StringVar(value=patron_seleccionado)

lista_ips = tk.Listbox(root, font=fuente_lista, height=8, selectbackground="#cce6ff")
lista_ips.pack(pady=12, fill=tk.X, padx=40)
lista_ips.bind("<Double-Button-1>", on_doble_click)

def inicializar_lista_ips():
    refrescar_lista_ips()

inicializar_lista_ips()

# Frame para todos los botones principales en una sola línea
frame_botones_principal = tk.Frame(root)
frame_botones_principal.pack(pady=14)

btn_gestionar_ficheros = tk.Button(frame_botones_principal, text="Gestionar ficheros", font=fuente_boton, bg="#5bc0de", fg="white", height=2, width=18, command=gestionar_ficheros)
btn_gestionar_ips = tk.Button(frame_botones_principal, text="Gestionar IPs", font=fuente_boton, bg="#0275d8", fg="white", height=2, width=16, command=gestionar_ips_personalizadas)
btn_gestionar_patrones = tk.Button(frame_botones_principal, text="Gestionar patrones", font=fuente_boton, bg="#d6b844", fg="white", height=2, width=18, command=gestionar_patrones)
btn_actualizar = tk.Button(frame_botones_principal, text="Actualizar archivos", font=fuente_boton, bg="#4caf50", fg="white", height=2, width=18, command=on_aceptar)
btn_salir = tk.Button(frame_botones_principal, text="Salir", font=fuente_boton, bg="#343a40", fg="white", height=2, width=10, command=on_cerrar)

for btn in [btn_gestionar_ficheros, btn_gestionar_ips, btn_gestionar_patrones, btn_actualizar, btn_salir]:
    btn.pack(side=tk.LEFT, padx=5)

tk.Label(root, text="Archivos a modificar:", font=fuente_grande).pack(pady=14)
frame_archivos = tk.Frame(root)
frame_archivos.pack(pady=7)

archivos_listbox = tk.Listbox(frame_archivos, font=fuente_archivos, width=85, height=5)
archivos_listbox.pack(side=tk.LEFT, padx=7)
refrescar_lista_archivos()

scrollbar = tk.Scrollbar(frame_archivos, orient="vertical", command=archivos_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
archivos_listbox.config(yscrollcommand=scrollbar.set)

tk.Label(root, text="Patrón de expresión regular usado:", font=fuente_grande).pack(pady=16)
frame_patron = tk.Frame(root)
frame_patron.pack(pady=4)
entry_patron = tk.Entry(frame_patron, textvariable=patron_var, font=fuente_patron, width=80, state='readonly', readonlybackground="#e9ecef")
entry_patron.pack(side=tk.LEFT, padx=7)

actualizar_estado_boton_actualizar()

root.protocol("WM_DELETE_WINDOW", on_cerrar)
log_event("Aplicación iniciada.")
root.mainloop()
