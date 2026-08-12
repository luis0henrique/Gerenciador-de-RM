import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import re


class ImportManager:
    """Gerencia a importação de alunos de arquivos .xlsx e .csv"""

    def __init__(self):
        self.accepted_extensions = ['.xlsx', '.csv']

    def importar_arquivo(self, file_path: str) -> Dict:
        """
        Importa dados de um arquivo .xlsx ou .csv

        Args:
            file_path: Caminho do arquivo a importar

        Returns:
            Dict com os dados importados e validações
        """
        path = Path(file_path)

        if path.suffix.lower() not in self.accepted_extensions:
            return {'sucesso': False, 'erro': 'Arquivo inválido. Use .xlsx ou .csv'}

        try:
            if path.suffix.lower() == '.xlsx':
                return self._importar_xlsx(file_path)
            else:
                return self._importar_csv(file_path)
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro ao ler arquivo: {str(e)}'}

    def _importar_xlsx(self, file_path: str) -> Dict:
        """Importa dados de um arquivo Excel"""
        try:
            df = pd.read_excel(file_path, header=None)

            if df.empty:
                return {'sucesso': False, 'erro': 'Arquivo Excel vazio'}

            # Detecta se há cabeçalho
            tem_cabecalho, linhas_dados = self._detect_header_xlsx(df)

            if len(linhas_dados) == 0:
                return {'sucesso': False, 'erro': 'Nenhum dado encontrado no arquivo Excel'}

            # Identifica as colunas de Nome e RM
            col_nome, col_rm = self._identify_columns_xlsx(linhas_dados)

            if col_nome is None or col_rm is None:
                return {'sucesso': False, 'erro': 'Não foi possível identificar colunas de Nome e RM'}

            # Extrai os dados
            alunos = []
            for idx, row in linhas_dados.iterrows():
                try:
                    nome = str(row.iloc[col_nome]).strip() if col_nome < len(row) else ""
                    rm = str(row.iloc[col_rm]).strip() if col_rm < len(row) else ""

                    if nome and rm and self._is_valid_rm(rm):
                        alunos.append((nome, rm))
                except (IndexError, KeyError, TypeError):
                    continue

            if not alunos:
                return {'sucesso': False, 'erro': 'Nenhum aluno válido encontrado no arquivo'}

            return {
                'sucesso': True,
                'alunos': alunos,
                'total': len(alunos),
                'tipo': 'xlsx'
            }

        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro ao processar Excel: {str(e)}'}

    def _detect_header_xlsx(self, df: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
        """Detecta se a primeira linha é um cabeçalho"""
        if df.empty or len(df) < 2:
            return False, df

        primeira_linha = df.iloc[0]
        segunda_linha = df.iloc[1]

        # Verifica se há algum RM válido na primeira linha
        primeira_tem_rm = any(
            self._is_valid_rm(str(val).strip())
            for val in primeira_linha if str(val).strip()
        )

        # Verifica se há algum RM válido na segunda linha
        segunda_tem_rm = any(
            self._is_valid_rm(str(val).strip())
            for val in segunda_linha if str(val).strip()
        )

        # Se a primeira linha não tem RM mas segunda tem, primeira é cabeçalho
        if not primeira_tem_rm and segunda_tem_rm:
            return True, df.iloc[1:].reset_index(drop=True)

        return False, df

    def _identify_columns_xlsx(self, df: pd.DataFrame) -> Tuple[Optional[int], Optional[int]]:
        """Identifica qual coluna tem nomes e qual tem RMs"""
        if df.empty or len(df.columns) < 2:
            return None, None

        col_nome = None
        col_rm = None

        # Itera sobre as primeiras 2 colunas
        for col_idx in range(min(2, len(df.columns))):
            col_data = df.iloc[:, col_idx]

            # Heurísticas para identificar nomes
            nome_score = 0
            rm_score = 0

            # Verifica primeiras 3 linhas
            for val in col_data.iloc[:min(3, len(col_data))]:
                val_str = str(val).strip()

                # Se é número válido de RM
                if self._is_valid_rm(val_str):
                    rm_score += 1
                # Se tem espaço ou caracteres de nome
                elif len(val_str) > 2 and (' ' in val_str or self._has_letters(val_str)):
                    nome_score += 1

            if nome_score > rm_score and col_nome is None:
                col_nome = col_idx
            elif rm_score > nome_score and col_rm is None:
                col_rm = col_idx

        # Se não identificou, tenta por posição (coluna 0 = nomes, coluna 1 = RMs)
        if col_nome is None:
            col_nome = 0
        if col_rm is None:
            col_rm = 1

        return col_nome, col_rm

    def _importar_csv(self, file_path: str) -> Dict:
        """Importa dados de um arquivo CSV com detecção de separador"""
        try:
            # Tenta detectar o separador
            separador = self._detect_csv_separator(file_path)

            df = pd.read_csv(file_path, sep=separador, header=None, dtype=str)

            if df.empty:
                return {'sucesso': False, 'erro': 'Arquivo CSV vazio'}

            # Detecta se há cabeçalho
            tem_cabecalho, linhas_dados = self._detect_header_csv(df)

            if len(linhas_dados) == 0:
                return {'sucesso': False, 'erro': 'Nenhum dado encontrado no arquivo CSV'}

            # Identifica as colunas
            col_nome, col_rm = self._identify_columns_csv(linhas_dados)

            if col_nome is None or col_rm is None:
                return {'sucesso': False, 'erro': 'Não foi possível identificar colunas de Nome e RM'}

            # Extrai os dados
            alunos = []
            for idx, row in linhas_dados.iterrows():
                try:
                    nome = str(row.iloc[col_nome]).strip() if col_nome < len(row) else ""
                    rm = str(row.iloc[col_rm]).strip() if col_rm < len(row) else ""

                    if nome and rm and self._is_valid_rm(rm):
                        alunos.append((nome, rm))
                except (IndexError, KeyError, TypeError):
                    continue

            if not alunos:
                return {'sucesso': False, 'erro': 'Nenhum aluno válido encontrado no arquivo'}

            return {
                'sucesso': True,
                'alunos': alunos,
                'total': len(alunos),
                'tipo': 'csv',
                'separador': separador
            }

        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro ao processar CSV: {str(e)}'}

    def _detect_csv_separator(self, file_path: str) -> str:
        """Detecta o separador do CSV (';' ou ',')"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                primeira_linha = f.readline()

            # Conta ocorrências de cada separador
            aspas = primeira_linha.count('"')
            ponto_virgula = primeira_linha.count(';')
            virgula = primeira_linha.count(',')

            # Se há aspas e mais de um ponto-virgula, é provavelmente CSV de PT
            if aspas > 0 or ponto_virgula > virgula:
                return ';'

            return ','
        except:
            return ';'  # Padrão para pt-BR

    def _detect_header_csv(self, df: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
        """Detecta se a primeira linha é um cabeçalho"""
        if df.empty or len(df) < 2:
            return False, df

        primeira_linha = df.iloc[0]
        segunda_linha = df.iloc[1] if len(df) > 1 else None

        if segunda_linha is None:
            return False, df

        # Verifica se há algum RM válido na primeira linha
        primeira_tem_rm = any(
            self._is_valid_rm(str(val).strip())
            for val in primeira_linha if str(val).strip()
        )

        # Verifica se há algum RM válido na segunda linha
        segunda_tem_rm = any(
            self._is_valid_rm(str(val).strip())
            for val in segunda_linha if str(val).strip()
        )

        # Se a primeira linha não tem RM mas segunda tem, primeira é cabeçalho
        if not primeira_tem_rm and segunda_tem_rm:
            return True, df.iloc[1:].reset_index(drop=True)

        return False, df

    def _identify_columns_csv(self, df: pd.DataFrame) -> Tuple[Optional[int], Optional[int]]:
        """Identifica qual coluna tem nomes e qual tem RMs"""
        if df.empty or len(df.columns) == 0:
            return None, None

        col_nome = None
        col_rm = None

        for col_idx in range(min(2, len(df.columns))):
            col_data = df.iloc[:, col_idx]

            nome_score = 0
            rm_score = 0

            for val in col_data[:min(3, len(col_data))]:  # Verifica primeiras 3 linhas
                val_str = str(val).strip()

                if self._is_valid_rm(val_str):
                    rm_score += 1
                elif len(val_str) > 2 and (self._has_letters(val_str) or ' ' in val_str):
                    nome_score += 1

            if nome_score > rm_score and col_nome is None:
                col_nome = col_idx
            elif rm_score > nome_score and col_rm is None:
                col_rm = col_idx

        # Se não identificou, assume padrão
        if col_nome is None:
            col_nome = 0
        if col_rm is None:
            col_rm = 1

        return col_nome, col_rm

    def _is_valid_rm(self, rm: str) -> bool:
        """Verifica se é um RM válido (número inteiro)"""
        try:
            int(rm)
            return True
        except ValueError:
            return False

    def _has_letters(self, text: str) -> bool:
        """Verifica se o texto contém letras"""
        return bool(re.search(r'[a-zA-ZÀ-ÿ]', text))

    def validar_alunos_importados(self, alunos: List[Tuple[str, str]], data_manager) -> Dict:
        """
        Valida alunos importados contra a base de dados

        Args:
            alunos: Lista de tuplas (nome, rm)
            data_manager: Gerenciador de dados para validação

        Returns:
            Dict com validações e alunos válidos
        """
        rms_duplicados = []
        rms_vistos = set()
        alunos_validos = []

        for nome, rm in alunos:
            try:
                rm_int = int(rm)
            except ValueError:
                continue

            # Verifica duplicata dentro da importação
            if rm_int in rms_vistos:
                rms_duplicados.append((rm_int, "Duplicado na importação"))
                continue

            # Verifica duplicata na database
            if data_manager and hasattr(data_manager, 'excel_manager'):
                if not data_manager.excel_manager.df.empty:
                    df = data_manager.excel_manager.df
                    if rm_int in df['RM'].values:
                        aluno_existente = df[df['RM'] == rm_int].iloc[0]['Nome do(a) Aluno(a)']
                        rms_duplicados.append((rm_int, aluno_existente))
                        continue

            rms_vistos.add(rm_int)
            alunos_validos.append((nome, rm_int))

        return {
            'alunos_validos': alunos_validos,
            'rms_duplicados': rms_duplicados,
            'total_importados': len(alunos),
            'total_validos': len(alunos_validos)
        }
