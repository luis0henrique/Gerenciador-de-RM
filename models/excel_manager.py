import pandas as pd
from pathlib import Path
from collections import defaultdict
from utils.helpers import remove_acentos

class ExcelManager:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Nome do Aluno', 'RM'])
        self.current_path = None
        self.rm_set = set()
        self.nome_index = defaultdict(list)
        
    def load_excel(self, file_path: str) -> bool:
        try:
            # Carrega em chunks para arquivos grandes
            if Path(file_path).stat().st_size > 10_000_000:
                chunks = pd.read_excel(file_path, chunksize=5000)
                self.df = pd.concat(chunks, ignore_index=True)
            else:
                self.df = pd.read_excel(file_path)
            
            # Pré-ordenação durante o carregamento
            self._build_indexes()
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def _build_indexes(self):
        """Constrói estruturas de índice para buscas rápidas"""
        self.rm_set = set(self.df['RM'].values)
        self.nome_index = defaultdict(list)
        
        for idx, row in self.df.iterrows():
            nome_normalizado = remove_acentos(str(row['Nome do Aluno']).lower())
            tokens = nome_normalizado.split()[:3]
            for token in tokens:
                if len(token) > 2:
                    self.nome_index[token].append((idx, nome_normalizado))

    def _preprocess_data(self):
        # Garantir tipos de dados consistentes
        self.df['RM'] = pd.to_numeric(self.df['RM'], errors='coerce').astype('Int64')
        self.df['Nome do Aluno'] = self.df['Nome do Aluno'].astype(str)
        
        # Remover linhas inválidas
        self.df = self.df.dropna(subset=['Nome do Aluno', 'RM'])
