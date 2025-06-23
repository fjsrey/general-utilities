import ctypes

def toggle_mouse_buttons():
    # Obtener el estado actual de los botones del ratón (0 = predeterminado, 1 = invertido)
    current_state = ctypes.windll.user32.GetSystemMetrics(23)
    
    # Invertir el estado actual
    new_state = 0 if current_state else 1
    
    # Aplicar el nuevo estado
    ctypes.windll.user32.SwapMouseButton(new_state)
    
    print(f"Botones del ratón intercambiados: {'Invertidos' if new_state else 'Normales'}")

if __name__ == "__main__":
    toggle_mouse_buttons()
