# poe2_schema.py - ESTRUTURA FINAL: Alinhada com o JSON esperado

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import json

# =======================================================
# 1. MODELO PARA DETALHES DE SKILL (Ação)
# =======================================================
class SkillDetails(BaseModel):
    """
    Representa uma skill ou ação realizada num determinado passo de leveling.
    As chaves estão alinhadas com o ficheiro de output JSON.
    """
    type: str = Field(description="O tipo de item/ação: 'Skill', 'Passive', 'Item'. Deve ser SEMPRE 'Skill' para este contexto.")
    name: str = Field(description="O nome exato da Skill Gem (ex: 'Earthquake', 'Shield Charge').")
    level: int = Field(description="O nível da Skill Gem, não o nível do personagem (Inteiro). Deve ser 1, 2, 3, etc.")
    passives: List[str] = Field(description="Uma LISTA de strings com os nomes das Passivas/Keystones/Notables adquiridas que são relevantes para esta skill neste passo. Use uma lista vazia [] se não houver nenhuma.")


# =======================================================
# 2. MODELO PARA PASSO DE LEVELING
# =======================================================
class LevelingStep(BaseModel):
    """
    Representa um passo específico na jornada de leveling, tipicamente um range de níveis.
    """
    level_range: str = Field(description="O range de nível coberto por este passo (e.g., '1-10', '40+').")
    actions: List[SkillDetails] = Field(description="Uma LISTA de objetos SkillDetails/ações realizadas neste range de nível.")


# =======================================================
# 3. MODELO PRINCIPAL DA BUILD
# =======================================================
class Poe2Build(BaseModel):
    """
    Representa a estrutura completa da Build extraída para o Path of Exile 2.
    """
    build_name: str = Field(description="O nome completo da build, extraído do título do artigo (ex: '[0.3] Warrior EARTHQUAKE Leveling Guide').")
    class_name: str = Field(alias='class', description="A classe principal da build (e.g., 'Warrior', 'Sorceress').")
    version: str = Field(description="A versão do patch do jogo (e.g., '0.3', 'Beta').")
    reputation: int = Field(description="Um inteiro de reputação simulada (placeholder: 95000) para ordenação, extraído do artigo se possível.")
    
    # Lista de passos de leveling
    skill_tree_leveling: List[LevelingStep] = Field(description="Uma LISTA ORDENADA de LevelingSteps que detalha o progresso da build por range de nível.")


# =======================================================
# 4. FUNÇÕES UTILITY PARA OLLAMA
# =======================================================

def get_poe2_build_schema_json() -> Dict[str, Any]:
    """Retorna o esquema JSON completo para a Poe2Build."""
    # O Pydantic cria o JSON Schema, incluindo as referências aninhadas (SkillDetails e LevelingStep)
    return Poe2Build.model_json_schema()

# Exemplo de como serializar o schema (opcional, apenas para verificar o JSON gerado)
if __name__ == '__main__':
    print("--- SCHEMA DE BUILD ---")
    print(json.dumps(get_poe2_build_schema_json(), indent=2))

    # Teste de um modelo válido para garantir que o alias 'class_name' funciona
    try:
        test_data = Poe2Build(
            build_name="Test Build",
            class_name="TestClass",
            version="1.0",
            reputation=100,
            skill_tree_leveling=[
                LevelingStep(
                    level_range="1-5",
                    actions=[
                        SkillDetails(type="Skill", name="TestSkill", level=1, passives=["TestPassive"])
                    ]
                )
            ]
        )
        # O método model_dump() (V2) ou dict() (V1) irá gerar a chave 'class' por causa do alias.
        print("\n--- TESTE DE MODELO COM ALIAS ---")
        # Usando by_alias=True para garantir que a chave 'class' é usada no output
        print(json.dumps(test_data.model_dump(by_alias=True), indent=2)) 
    except Exception as e:
        print(f"Erro ao testar a criação do modelo: {e}")
