import pandas as pd
from difflib import SequenceMatcher
from collections import defaultdict
from typing import Dict, Any, Optional, List
from utils.helpers import remove_acentos, formatar_nome, extrair_sobrenome

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
        return int(rm) in self.rm_set

    def get_aluno_por_rm(self, rm) -> Optional[Dict[str, Any]]:
        """Obtém aluno por RM com tratamento de erro"""
        try:
            aluno = self.excel_manager.df[self.excel_manager.df['RM'] == int(rm)].iloc[0]
            return aluno.to_dict()
        except (IndexError, KeyError, ValueError):
            return None

    def adicionar_aluno(self, nome: str, rm: int) -> bool:
        """Adiciona aluno com validação e atualização de índices"""
        if not hasattr(self.excel_manager, 'df'):
            return False

        nome_formatado = formatar_nome(nome)
        sobrenome = extrair_sobrenome(nome_formatado)
        try:
            rm_int = int(rm)
        except Exception:
            return False

        # Cria novo registro com as 3 colunas
        new_row = pd.DataFrame([[sobrenome, nome_formatado, rm_int]], columns=self.excel_manager.df.columns)
        self.excel_manager.df = pd.concat([self.excel_manager.df, new_row], ignore_index=True)
        self._build_indexes()
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

        melhor_match = None
        melhor_similaridade = threshold

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

    def validar_alunos_em_lote(self, alunos: List):
        """Executa todas as validações em lote"""
        problemas_rm = []
        rms_duplicados = []
        duplicatas = []
        alunos_validos = []
        rms_vistos = set()

        for linha, nome, rm in alunos:
            # RM validation
            if not str(rm).isdigit():
                problemas_rm.append(f"Linha {linha}: RM '{rm}' não é numérico")
                continue

            rm_int = int(rm)

            # Check for duplicate RMs in current input
            if rm_int in rms_vistos:
                rms_duplicados.append((rm_int, f"Duplicado na linha {linha}"))
                continue
            rms_vistos.add(rm_int)

            # Check for existing RM in database
            if self.rm_existe(rm_int):
                aluno_existente = self.get_aluno_por_rm(rm_int)
                rms_duplicados.append((rm_int, aluno_existente['Nome do(a) Aluno(a)'] if aluno_existente else ""))
                continue

            # Check for similar names
            similar_check = self.nome_similar_existe(nome)
            if similar_check.get('similar', False):
                duplicatas.append({
                    'linha': linha,
                    'nome_novo': nome,
                    'rm_novo': rm_int,
                    'nome_existente': similar_check['nome_existente'],
                    'rm_existente': similar_check['rm_existente'],
                    'similarity': similar_check['similarity']
                })

            alunos_validos.append((nome, rm_int))

        return {
            'problemas_rm': problemas_rm,
            'rms_duplicados': rms_duplicados,
            'duplicatas': duplicatas,
            'alunos_validos': alunos_validos
        }

    def remover_alunos(self, alunos: List[Dict[str, Any]]) -> bool:
        """Remove alunos com base em uma lista de dicionários contendo RM e Nome"""
        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            return False

        try:
            rms_para_remover = {int(aluno['RM']) for aluno in alunos}
            original_size = len(self.excel_manager.df)
            self.excel_manager.df = self.excel_manager.df[~self.excel_manager.df['RM'].isin(rms_para_remover)].reset_index(drop=True)
            if len(self.excel_manager.df) == original_size:
                return False
            self._build_indexes()
            return True
        except Exception as e:
            print(f"Erro ao remover alunos: {e}")
            return False