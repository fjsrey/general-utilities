#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cronómetro con pausa/reanudación, reset y persistencia en Cronometro.yml (en la misma carpeta)
"""

import tkinter as tk
from datetime import datetime, timedelta
import os
import yaml

class CronometroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cronómetro")
        self.root.resizable(False, False)  # Deshabilita maximizar y redimensionar

        self.start_time = None
        self.elapsed = timedelta()
        self.running = True  # Empieza contando automáticamente
        self.pause_start = None
        self.total_paused = timedelta()
        self.reset_clicks = 0
        self.last_reset_time = None
        self.carry_elapsed = timedelta()
        self.blink_state = False  # Estado para el parpadeo

        self.yml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Cronometro.yml")
        self.load_data()

        # Inicia el conteo automáticamente
        if not self.running:  # Por si acaso, aunque ahora empieza contando
            self.running = True
        self.start_time = datetime.now()

        self.lbl_carry = tk.Label(self.root, text=f"Acumulado: {self.formatear_tiempo(self.carry_elapsed)}", font=("Arial", 20))
        self.lbl_carry.pack(pady=5)

        self.lbl_elapsed = tk.Label(self.root, text=self.formatear_tiempo(self.elapsed), font=("Arial", 24))
        self.lbl_elapsed.pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.btn_play = tk.Button(frame, text="Play", width=10, command=self.play, state=tk.DISABLED)
        self.btn_play.grid(row=0, column=0, padx=5)

        self.btn_pause = tk.Button(frame, text="Pause", width=10, command=self.pause, state=tk.NORMAL)
        self.btn_pause.grid(row=0, column=1, padx=5)

        self.btn_reset = tk.Button(frame, text="Reset", width=10, command=self.reset)
        self.btn_reset.grid(row=0, column=2, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_timer()
        self.root.mainloop()

    def formatear_tiempo(self, td):
        total_seconds = int(td.total_seconds())
        hours, rem = divmod(total_seconds, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def formatear_hora(self, dt):
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def load_data(self):
        if os.path.exists(self.yml_path):
            with open(self.yml_path, "r") as f:
                data = yaml.safe_load(f)
                if data:
                    self.elapsed = timedelta(seconds=data.get("elapsed_seconds", 0))
                    self.carry_elapsed = timedelta(seconds=data.get("carry_elapsed_seconds", 0))
        
        self.startup_time = datetime.now()

    def save_data(self):
        if self.running:
            self.elapsed += datetime.now() - self.start_time - self.total_paused
        data = {
            "elapsed_seconds": int(self.elapsed.total_seconds()),
            "carry_elapsed_seconds": int(self.carry_elapsed.total_seconds())
        }
        with open(self.yml_path, "w") as f:
            yaml.dump(data, f)

    def play(self):
        if not self.running:
            self.running = True
            
            self.start_time = datetime.now()
            
            #if self.pause_start:
            #    self.total_paused += datetime.now() - self.pause_start
            
            self.pause_start = None
            self.btn_play.config(state=tk.DISABLED)
            self.btn_pause.config(state=tk.NORMAL)
            
            # Detener el parpadeo
            self.blink_state = False
            self.lbl_elapsed.config(fg="black")

    def pause(self):
        if self.running:
            self.running = False
            self.pause_start = datetime.now()
            self.elapsed += datetime.now() - self.start_time - self.total_paused
            self.btn_play.config(state=tk.NORMAL)
            self.btn_pause.config(state=tk.DISABLED)
            # Iniciar el parpadeo
            self.blink_state = True
            self.blink_timer()

    def blink_timer(self):
        if self.blink_state:
            if self.lbl_elapsed.cget("fg") == "black":
                self.lbl_elapsed.config(fg="red")
            else:
                self.lbl_elapsed.config(fg="black")
            self.root.after(500, self.blink_timer)

    def reset(self):
        now = datetime.now()
        if self.last_reset_time and (now - self.last_reset_time).total_seconds() < 1:
            self.reset_clicks += 1
        else:
            self.reset_clicks = 1
        self.last_reset_time = now
 
        self.carry_elapsed += self.elapsed + (datetime.now() - self.start_time - self.total_paused if self.running else timedelta())
        self.lbl_carry.config(text=f"Acumulado: {self.formatear_tiempo(self.carry_elapsed)}")

        if self.reset_clicks >= 2:
            self.carry_elapsed = timedelta()
            self.lbl_carry.config(text=f"Acumulado: {self.formatear_tiempo(self.carry_elapsed)}")

        # Asignar un tiempo de 00:00:00
        self.elapsed = timedelta()


        self.total_paused = timedelta()
        if self.running:
            self.start_time = datetime.now()
            self.pause_start = None
        else:
            self.start_time = None
            self.pause_start = None

    def update_timer(self):
        if self.running and self.start_time:
            current = datetime.now() - self.start_time - self.total_paused
            display = self.elapsed + current
        else:
            display = self.elapsed
        if self.running or not self.blink_state:
            self.lbl_elapsed.config(text=self.formatear_tiempo(display))
        self.root.after(1000, self.update_timer)

    def on_close(self):
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    CronometroApp()
