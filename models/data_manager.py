import pandas as pd
from difflib import SequenceMatcher
from collections import defaultdict
from typing import Dict, Any, Optional
from utils.helpers import remove_acentos, formatar_nome

class DataManager:
    def __init__(self, excel_manager):
        self.excel_manager = excel_manager
        self.rm_set = set()
        self.nome_index = defaultdict(list)
        self._build_indexes()

    def _build_indexes(self):
        """Constrói índices otimizados para busca"""
        self.rm_set.clear()
        self.nome_index.clear()

        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            return

        # Preenche o conjunto de RMs
        self.rm_set.update(self.excel_manager.df['RM'].dropna().unique())

        # Cria índice invertido para nomes sem modificar o DataFrame original
        for idx, row in self.excel_manager.df.iterrows():
            nome_normalizado = remove_acentos(str(row['Nome do(a) Aluno(a)'])).lower()
            tokens = nome_normalizado.split()[:3]
            for token in (t for t in tokens if len(t) > 2):
                self.nome_index[token].append((idx, nome_normalizado))

    def rm_existe(self, rm) -> bool:
        """Verificação otimizada de existência de RM"""
        return rm in self.rm_set

    def get_aluno_por_rm(self, rm) -> Optional[Dict[str, Any]]:
        """Obtém aluno por RM com tratamento de erro"""
        try:
            aluno = self.excel_manager.df[self.excel_manager.df['RM'] == rm].iloc[0]
            return aluno.to_dict()
        except (IndexError, KeyError):
            return None

    def adicionar_aluno(self, nome: str, rm: int) -> bool:
        """Adiciona aluno com validação e atualização de índices"""
        if not hasattr(self.excel_manager, 'df'):
            return False

        # Formata o nome antes de adicionar
        nome_formatado = formatar_nome(nome)

        # Cria novo registro
        new_row = pd.DataFrame([[nome_formatado, rm]], columns=self.excel_manager.df.columns)
        self.excel_manager.df = pd.concat([self.excel_manager.df, new_row], ignore_index=True)

        # Atualiza índices
        nome_normalizado = remove_acentos(str(nome).lower())
        tokens = nome_normalizado.split()[:3]
        for token in (t for t in tokens if len(t) > 2):
            self.nome_index[token].append((len(self.excel_manager.df)-1, nome_normalizado))
        self.rm_set.add(rm)

        return True

    def nome_similar_existe(self, nome_novo: str, threshold: float = 0.8) -> Dict[str, Any]:
        """Busca por nomes similares com índice otimizado"""
        nome_novo_normalizado = remove_acentos(nome_novo.lower())
        tokens_relevantes = [t for t in nome_novo_normalizado.split()[:3] if len(t) > 2]

        # Busca candidatos usando o índice invertido
        candidatos = set()
        for token in tokens_relevantes:
            for idx, nome_existente in self.nome_index.get(token, []):
                candidatos.add((idx, nome_existente))

        if not candidatos:
            return {'similar': False, 'nome_existente': None, 'rm_existente': None, 'similarity': 0}

        # Comparação apenas com candidatos relevantes
        melhor_match = None
        melhor_similaridade = threshold  # Começa com o threshold mínimo

        for idx, nome_existente_normalizado in candidatos:
            similarity = SequenceMatcher(None, nome_novo_normalizado, nome_existente_normalizado).ratio()

            if similarity > melhor_similaridade:
                melhor_similaridade = similarity
                melhor_match = {
                    'nome_existente': self.excel_manager.df.iloc[idx]['Nome do(a) Aluno(a)'],
                    'rm_existente': self.excel_manager.df.iloc[idx]['RM'],
                    'similarity': similarity
                }

        if melhor_match:
            return {'similar': True, **melhor_match}

        return {'similar': False, 'nome_existente': None, 'rm_existente': None, 'similarity': 0}