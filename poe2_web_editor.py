# poe2_web_editor.py (Agora no modo de Visualização Apenas)

from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)
# Não é necessário app.secret_key nem 'flash' porque não há formulários de edição/submissão

# Definições (copiadas dos seus outros ficheiros)
BUILD_FILE = "poe2_builds.json"
POE2_CLASSES = [
    "Warrior", "Monk", "Mercenary", "Sorceress", "Witch", "Ranger",
    "Huntress", "Druid", "Duelist", "Marauder", "Shadow", "Templar"
]
LEVEL_RANGES = ["1-5", "6-10", "11-20", "21-40"]

def load_builds():
    """Carrega os dados da build a partir do ficheiro JSON."""
    if not os.path.exists(BUILD_FILE) or os.path.getsize(BUILD_FILE) == 0:
        return {}
    with open(BUILD_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# === ROTAS WEB ===

@app.route('/', methods=['GET', 'POST'])
def index():
    """Página inicial para selecionar a classe."""
    if request.method == 'POST':
        selected_class = request.form.get('class_selector')
        if selected_class:
            # Redireciona para a rota de visualização
            return redirect(url_for('view_build', class_name=selected_class))
        
    return render_template('index.html', classes=POE2_CLASSES)

@app.route('/edit/<class_name>')
def view_build(class_name):
    """Página de visualização (anteriormente 'edit') da build."""
    builds = load_builds()
    # Assume que só tem 1 build por classe
    build_list = builds.get(class_name, [])
    
    if not build_list:
        # Fornece dados vazios se não houver build para evitar falhas no template
        build_data = {"reputation": "N/A", "levels": {range_str: [] for range_str in LEVEL_RANGES}}
    else:
        build_data = build_list[0]
        
    # Usa 'edit_build.html' como pedido, mas o conteúdo é de visualização
    return render_template('edit_build.html', 
                           class_name=class_name, 
                           build=build_data, 
                           level_ranges=LEVEL_RANGES)

if __name__ == '__main__':
    # É necessário ter o Flask instalado: pip install Flask
    # Certifique-se que o ficheiro poe2_web_editor.py e a pasta templates estão lado a lado.
    app.run(debug=True)