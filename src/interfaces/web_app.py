# poe2_web_editor.py (Agora no modo de Visualização Apenas)

from flask import Flask, render_template, request, redirect, url_for
import json
import os
from pathlib import Path
import config
import re

# Ensure Flask will find the templates folder at the project root
template_folder = str(Path(__file__).resolve().parents[2] / 'templates')
app = Flask(__name__, template_folder=template_folder)
# Não é necessário app.secret_key nem 'flash' porque não há formulários de edição/submissão

# Definições (copiadas dos seus outros ficheiros)
BUILD_FILE = config.BUILD_FILE
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
        # Provide empty data if no build exists to avoid template failures
        build_data = {"reputation": "N/A", "levels": {range_str: [] for range_str in LEVEL_RANGES}}
    else:
        raw = build_list[0]

        # Prepare buckets. If USE_ACT_BUCKETS is True, pre-create Act buckets in configured order.
        buckets = {}
        if config.USE_ACT_BUCKETS:
            for act_label in config.ACT_LEVEL_BUCKETS.keys():
                buckets[act_label] = []

        # Helper to add actions to a bucket label (creates the bucket if missing)
        def add_to_bucket(label, action_item):
            if label not in buckets:
                buckets[label] = []
            buckets[label].append(action_item)

        for step in raw.get('skill_tree_leveling', []):
            rng = step.get('level_range', 'Full Leveling')

            # collect actions that are skills
            actions = []
            for action in step.get('actions', []):
                if action.get('type') == 'Skill':
                    actions.append({
                        'skill_name': action.get('name', 'N/A'),
                        'required_level': action.get('level', 0),
                        'passives_acquired': action.get('passives', []) if isinstance(action.get('passives', []), list) else []
                    })

            if not actions:
                # Nothing to store for this step
                continue

            placed = False

            # Case 1: explicit Act labels inside the range string (e.g., 'Act 2', 'Act 2-Act 3', 'Act 3+')
            act_nums = re.findall(r'Act\s*(\d+)', rng, flags=re.IGNORECASE)
            if act_nums:
                # Add this step's actions to all referenced Acts
                for n in act_nums:
                    label = f"Act {int(n)}"
                    for skill_item in actions:
                        add_to_bucket(label, skill_item)
                placed = True

            if not placed and config.USE_ACT_BUCKETS:
                # Case 2: try to extract a numeric lower bound and map to configured act buckets
                m = re.search(r'(\d+)', rng)
                if m:
                    lower = int(m.group(1))
                    for act_label, (amin, amax) in config.ACT_LEVEL_BUCKETS.items():
                        if amin <= lower <= amax:
                            for skill_item in actions:
                                add_to_bucket(act_label, skill_item)
                            placed = True
                            break

            if not placed:
                # Fallback: use the original range string as its own bucket
                for skill_item in actions:
                    add_to_bucket(rng, skill_item)

        # Post-process buckets: deduplicate and sort skills by required_level
        for label, skills in list(buckets.items()):
            seen = set()
            unique_skills = []
            for s in skills:
                key = (s.get('skill_name'), s.get('required_level'))
                if key in seen:
                    continue
                seen.add(key)
                unique_skills.append(s)
            # sort by required_level (safe default 0)
            unique_skills.sort(key=lambda x: (x.get('required_level') or 0))
            buckets[label] = unique_skills

        build_data = raw.copy()
        build_data['levels'] = buckets
        
    # Usa 'edit_build.html' como pedido, mas o conteúdo é de visualização
    # Pass dynamic buckets derived from the build steps (e.g., 'Act 1', '1-10')
    return render_template('edit_build.html',
                           class_name=class_name,
                           build=build_data,
                           level_ranges=list(build_data.get('levels', {}).keys()))


@app.route('/debug/levels/<class_name>')
def debug_levels(class_name):
    """Debug endpoint: return the normalized build['levels'] for the given class as JSON."""
    builds = load_builds()
    build_list = builds.get(class_name, [])
    if not build_list:
        return ({'error': 'no build for class'}, 404)
    raw = build_list[0]
    # Reuse the same normalization logic by temporarily calling view_build logic path
    # We'll duplicate minimal normalization here to avoid making view_build a library function.
    buckets = {}
    if config.USE_ACT_BUCKETS:
        for act_label in config.ACT_LEVEL_BUCKETS.keys():
            buckets[act_label] = []

    def add_to_bucket(label, action_item):
        if label not in buckets:
            buckets[label] = []
        buckets[label].append(action_item)

    import re as _re
    for step in raw.get('skill_tree_leveling', []):
        rng = step.get('level_range', 'Full Leveling')
        actions = []
        for action in step.get('actions', []):
            if action.get('type') == 'Skill':
                actions.append({
                    'skill_name': action.get('name', 'N/A'),
                    'required_level': action.get('level', 0),
                    'passives_acquired': action.get('passives', []) if isinstance(action.get('passives', []), list) else []
                })
        if not actions:
            continue

        placed = False
        act_nums = _re.findall(r'Act\\s*(\\d+)', rng, flags=_re.IGNORECASE)
        if act_nums:
            for n in act_nums:
                label = f"Act {int(n)}"
                for skill_item in actions:
                    add_to_bucket(label, skill_item)
            placed = True

        if not placed and config.USE_ACT_BUCKETS:
            m = _re.search(r'(\\d+)', rng)
            if m:
                lower = int(m.group(1))
                for act_label, (amin, amax) in config.ACT_LEVEL_BUCKETS.items():
                    if amin <= lower <= amax:
                        for skill_item in actions:
                            add_to_bucket(act_label, skill_item)
                        placed = True
                        break

        if not placed:
            for skill_item in actions:
                add_to_bucket(rng, skill_item)

    # Deduplicate and sort
    for label, skills in list(buckets.items()):
        seen = set()
        unique_skills = []
        for s in skills:
            key = (s.get('skill_name'), s.get('required_level'))
            if key in seen:
                continue
            seen.add(key)
            unique_skills.append(s)
        unique_skills.sort(key=lambda x: (x.get('required_level') or 0))
        buckets[label] = unique_skills

    return buckets

if __name__ == '__main__':
    # É necessário ter o Flask instalado: pip install Flask
    # Certifique-se que o ficheiro poe2_web_editor.py e a pasta templates estão lado a lado.
    app.run(debug=True)