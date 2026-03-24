# poe2_app_viewer.py (Apenas para visualização)

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

# Definições
BUILD_FILE = "poe2_builds.json"
POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", "Ranger",
    "Huntress", "Druid", "Duelist", "Marauder", "Shadow", "Templar"
]
LEVEL_RANGES = ["1-5", "6-10", "11-20", "21-40"]

def load_builds():
    if not os.path.exists(BUILD_FILE) or os.path.getsize(BUILD_FILE) == 0:
        return {}
    with open(BUILD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

class BuildViewerApp:
    def __init__(self, master):
        self.master = master
        master.title("Path of Exile 2 Build Viewer")

        # Configurar estilos (mantemos os tamanhos que gostou)
        self.style = ttk.Style()
        self.style.configure('Header.TLabel', font=('Arial', 14)) 
        self.style.configure('Header.TCombobox', font=('Arial', 14, 'bold'))
        self.style.configure('TNotebook.Tab', font=('Arial', 12, 'bold'), padding=[15, 5])
        
        # 1. Carregar dados
        self.builds_data = load_builds()
        self.current_class = tk.StringVar(master)
        self.current_class.set(POE2_CLASSES[0])

        # 2. Configurar a Interface
        self.create_widgets(master)
        self.load_class_data(POE2_CLASSES[0])

    def create_widgets(self, master):
        # Frame de Seleção de Classe
        class_frame = ttk.Frame(master, padding="10")
        class_frame.pack(fill='x')

        ttk.Label(class_frame, text="Classe:", style='Header.TLabel').pack(side='left', padx=5)
        
        # Dropdown para selecionar a classe
        self.class_menu = ttk.Combobox(class_frame, 
                                       textvariable=self.current_class, 
                                       values=POE2_CLASSES, 
                                       state="readonly", 
                                       style='Header.TCombobox')
        self.class_menu.pack(side='left', padx=5, fill='x', expand=True)
        self.class_menu.bind("<<ComboboxSelected>>", self.on_class_select)

        # Removemos o botão "GUARDAR ALTERAÇÕES"
        
        # Área de Visualização (Notebook para os Level Ranges)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, fill='both', expand=True)
        
        self.level_frames = {} 
        
        for range_str in LEVEL_RANGES:
            frame = ttk.Frame(self.notebook, padding="10")
            self.notebook.add(frame, text=f"Lvl {range_str}")
            self.level_frames[range_str] = frame
            self.create_level_widgets(frame, range_str)

    def create_level_widgets(self, frame, range_str):
        # Tabela (Treeview) para mostrar as Skills
        tree = ttk.Treeview(frame, columns=("Skill Name", "Required Level", "Passives Acquired"), show="headings")
        tree.heading("Skill Name", text="Skill Name")
        tree.column("Skill Name", width=150)
        tree.heading("Required Level", text="Level Mínimo")
        tree.column("Required Level", width=100, anchor='center')
        tree.heading("Passives Acquired", text="Passivas Adquiridas")
        tree.pack(fill='both', expand=True)
        self.level_frames[range_str].tree = tree
        
        # Removemos o frame para adicionar nova skill
        
    def on_class_select(self, event):
        selected_class = self.current_class.get()
        self.load_class_data(selected_class)
        
    def load_class_data(self, cls):
        # Limpa todas as treeviews
        for range_str in LEVEL_RANGES:
            tree = self.level_frames[range_str].tree
            for item in tree.get_children():
                tree.delete(item)
        
        # Carrega a build
        build_list = self.builds_data.get(cls, [])
        if not build_list:
            messagebox.showinfo("Informação", f"Nenhuma build encontrada para {cls}.")
            return

        current_build = build_list[0] 
        
        # Preenche as treeviews com os dados do build
        levels = current_build.get("levels", {})
        for range_str in LEVEL_RANGES:
            skills = levels.get(range_str, [])
            tree = self.level_frames[range_str].tree
            for skill in skills:
                passives_str = ", ".join(skill.get("passives_acquired", []))
                tree.insert("", "end", values=(
                    skill.get("skill_name", "N/A"),
                    skill.get("required_level", "N/A"),
                    passives_str
                ))

if __name__ == "__main__":
    root = tk.Tk()
    app = BuildViewerApp(root)
    root.mainloop()