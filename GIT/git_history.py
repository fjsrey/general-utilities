# pip install GitPython
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from git import Repo, NULL_TREE
from git.exc import GitError, InvalidGitRepositoryError, NoSuchPathError

def show_file_history():
    file_path = entry_file_path.get().strip()
    if not file_path:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.INSERT, "Por favor, introduce la ruta de un fichero.")
        return

    try:
        repo = Repo('.')  # Repositorio Git en el directorio actual
        commits = list(repo.iter_commits(paths=file_path))

        text_area.delete(1.0, tk.END)

        if not commits:
            text_area.insert(tk.INSERT, f"No se encontraron commits para el archivo: {file_path}")
            return

        for commit in commits:
            text_area.insert(tk.INSERT, f"Commit: {commit.hexsha}\n")
            text_area.insert(tk.INSERT, f"Author: {commit.author.name}\n")
            text_area.insert(tk.INSERT, f"Date: {commit.committed_datetime}\n")
            text_area.insert(tk.INSERT, f"Message: {commit.message.strip()}\n\n")

            if commit.parents:
                parent = commit.parents[0]
                diff_text = repo.git.diff(f"{parent.hexsha}..{commit.hexsha}", '--', file_path)
            else:
                diff_text = repo.git.show(commit.hexsha, '--', file_path)

            if diff_text.strip():
                text_area.insert(tk.INSERT, "Changes:\n")
                text_area.insert(tk.INSERT, diff_text + "\n")
            else:
                text_area.insert(tk.INSERT, "[Sin diferencias visibles en este commit.]\n")

            text_area.insert(tk.INSERT, "\n" + "=" * 100 + "\n\n")

    except InvalidGitRepositoryError:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.INSERT, "No se encontró un repositorio Git en el directorio actual.")
    except NoSuchPathError:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.INSERT, f"No se encontró el archivo: {file_path}")
    except GitError as e:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.INSERT, f"Error al acceder al repositorio Git: {e}")
    except Exception as e:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.INSERT, f"Error inesperado: {e}")

def copiar_al_portapapeles():
    contenido = text_area.get(1.0, tk.END).strip()
    if contenido:
        root.clipboard_clear()
        root.clipboard_append(contenido)
        messagebox.showinfo("Copiado", "El contenido se ha copiado al portapapeles.")
    else:
        messagebox.showwarning("Vacío", "No hay contenido para copiar.")

def exportar_a_txt():
    contenido = text_area.get(1.0, tk.END).strip()
    if not contenido:
        messagebox.showwarning("Vacío", "No hay contenido para exportar.")
        return

    archivo = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Archivo de texto", "*.txt")],
        title="Guardar como"
    )
    if archivo:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(contenido)
            messagebox.showinfo("Exportado", f"Archivo guardado correctamente:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

def seleccionar_archivo():
    archivo = filedialog.askopenfilename(title="Seleccionar archivo")
    if archivo:
        entry_file_path.delete(0, tk.END)
        entry_file_path.insert(0, archivo)
        show_file_history()

def on_drop(event):
    try:
        archivo = event.data.strip().strip("{}")  # Limpia posibles caracteres extra
        if archivo:
            entry_file_path.delete(0, tk.END)
            entry_file_path.insert(0, archivo)
            show_file_history()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo arrastrado:\n{e}")

# Crear la ventana principal
root = tk.Tk()
root.title("Historial de Modificaciones en Git")
root.geometry("1000x700")
root.minsize(800, 500)
root.columnconfigure(1, weight=1)
root.rowconfigure(1, weight=1)

# Permitir arrastrar y soltar archivos
try:
    root.tk.call('tk', 'dnd', 'enable')  # Activar soporte DnD
    root.drop_target_register(tk.DND_FILES)
    root.dnd_bind('<<Drop>>', on_drop)
except:
    pass  # Si el sistema no soporta DnD, no falla

# Etiqueta y campo de entrada
label = ttk.Label(root, text="Ruta y nombre del fichero:")
label.grid(column=0, row=0, padx=10, pady=10, sticky='w')

entry_file_path = ttk.Entry(root, width=50)
entry_file_path.grid(column=1, row=0, padx=10, pady=10, sticky='ew')

boton_buscar = ttk.Button(root, text="Buscar...", command=seleccionar_archivo)
boton_buscar.grid(column=2, row=0, padx=5, pady=10, sticky='ew')

boton_mostrar = ttk.Button(root, text="Aceptar", command=show_file_history)
boton_mostrar.grid(column=3, row=0, padx=5, pady=10, sticky='ew')

# Área de texto con scroll
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.grid(column=0, row=1, columnspan=4, padx=10, pady=(0, 10), sticky='nsew')

# Botones inferiores
frame_botones = ttk.Frame(root)
frame_botones.grid(column=0, row=2, columnspan=4, pady=(0, 15))

btn_copiar = ttk.Button(frame_botones, text="Copiar al portapapeles", command=copiar_al_portapapeles)
btn_copiar.pack(side=tk.LEFT, padx=10)

btn_exportar = ttk.Button(frame_botones, text="Exportar a .txt", command=exportar_a_txt)
btn_exportar.pack(side=tk.LEFT, padx=10)

# Iniciar el bucle principal de la aplicación
root.mainloop()
