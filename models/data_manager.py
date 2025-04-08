import pandas as pd
from difflib import SequenceMatcher
from utils.helpers import remove_acentos
from collections import defaultdict

class DataManager:
    def __init__(self, excel_manager):
        self.excel_manager = excel_manager
        self._build_indexes()

    def _build_indexes(self):
        """Constrói estruturas de índice para buscas rápidas"""
        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            self.rm_set = set()
            self.nome_index = defaultdict(list)
            return

        # Conjunto de RMs para verificação rápida
        self.rm_set = set(self.excel_manager.df['RM'].values)

        # Índice de nomes normalizados para similaridade
        self.nome_index = defaultdict(list)
        for idx, row in self.excel_manager.df.iterrows():
            nome_normalizado = remove_acentos(str(row['Nome do(a) Aluno(a)']).lower())
            # Armazena apenas os primeiros 3 tokens para otimização
            tokens = nome_normalizado.split()[:3]
            for token in tokens:
                if len(token) > 2:  # Ignora palavras muito curtas
                    self.nome_index[token].append((idx, nome_normalizado))

    def rm_existe(self, rm):
        """Verifica se RM já existe - O(1)"""
        return rm in self.rm_set

    def get_aluno_por_rm(self, rm):
        """Retorna dados do aluno pelo RM"""
        aluno = self.excel_manager.df[self.excel_manager.df['RM'] == rm].iloc[0]
        return aluno.to_dict()

    def adicionar_aluno(self, nome, rm):
        """Adiciona aluno ao DataFrame e atualiza índices"""
        if not hasattr(self.excel_manager, 'df'):
            raise Exception("DataFrame não foi carregado")

        # Adiciona ao Excel
        new_row = pd.DataFrame([[nome, rm]], columns=self.excel_manager.df.columns)
        self.excel_manager.df = pd.concat([self.excel_manager.df, new_row], ignore_index=True)

        # Atualiza índices
        self.rm_set.add(rm)
        nome_normalizado = remove_acentos(str(nome).lower())
        tokens = nome_normalizado.split()[:3]
        for token in tokens:
            if len(token) > 2:
                self.nome_index[token].append((len(self.excel_manager.df)-1, nome_normalizado))

    def nome_similar_existe(self, nome_novo, threshold=0.8):
        """Verificação otimizada de similaridade de nomes"""
        nome_novo_normalizado = remove_acentos(nome_novo.lower())

        # Extrai tokens relevantes para busca
        tokens = nome_novo_normalizado.split()[:3]
        tokens_relevantes = [t for t in tokens if len(t) > 2]

        # Conjunto de índices candidatos para verificação
        candidatos = set()
        for token in tokens_relevantes:
            for idx, _ in self.nome_index.get(token, []):
                candidatos.add(idx)

        # Se não encontrou candidatos, retorna imediatamente
        if not candidatos:
            return {'similar': False}

        # Verifica apenas os candidatos relevantes
        melhor_similaridade = 0
        melhor_match = None

        for idx in candidatos:
            nome_existente = remove_acentos(str(self.excel_manager.df.iloc[idx]['Nome do(a) Aluno(a)']).lower())
            similarity = SequenceMatcher(None, nome_novo_normalizado, nome_existente).quick_ratio()

            if similarity >= threshold:
                if similarity > melhor_similaridade:
                    melhor_similaridade = similarity
                    melhor_match = {
                        'nome_existente': self.excel_manager.df.iloc[idx]['Nome do(a) Aluno(a)'],
                        'rm_existente': self.excel_manager.df.iloc[idx]['RM'],
                        'similarity': similarity
                    }

        if melhor_match:
            melhor_match['similar'] = True
            return melhor_match

        return {'similar': False}