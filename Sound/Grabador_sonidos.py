import sounddevice as sd
import numpy as np
import wave
import os
import keyboard
from datetime import datetime

def nombre_archivo():
    base = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    contador = 0
    while True:
        nombre = f"{base}_Grabacion_{contador:03d}.wav"
        if not os.path.exists(nombre):
            return nombre
        contador += 1

def grabar_audio():
    print("Grabando... Presiona ESC para detener")
    fs = 44100
    dispositivos = sd.query_devices()
    
    # Selección de dispositivo de loopback
    dispositivo = next((d['index'] for d in dispositivos 
                      if 'loopback' in d['name'].lower()), None)
    
    audio_buffer = []  # Buffer para almacenar los frames
    
    def callback(indata, frame_count, time_info, status):
        audio_buffer.append(indata.copy())  # Almacenar datos de audio
    
    with sd.InputStream(device=dispositivo,
                       samplerate=fs,
                       channels=2,
                       dtype='int16',
                       callback=callback):
        keyboard.wait('esc')
    
    return np.concatenate(audio_buffer) if audio_buffer else np.array([])

def guardar_wav(nombre, audio):
    with wave.open(nombre, 'wb') as archivo:
        archivo.setnchannels(2)
        archivo.setsampwidth(2)
        archivo.setframerate(44100)
        archivo.writeframes(audio.tobytes())

if __name__ == "__main__":
    archivo = nombre_archivo()
    audio = grabar_audio()
    if audio.size > 0:
        guardar_wav(archivo, audio)
        print(f"Archivo guardado: {archivo}")
    else:
        print("Error: No se capturó audio")
