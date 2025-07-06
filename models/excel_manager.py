import pandas as pd
from pathlib import Path

class ExcelManager:
    def __init__(self):
        # Ordem padronizada das colunas
        self.columns = ['Sobrenome', 'Nome do(a) Aluno(a)', 'RM']
        self.df = pd.DataFrame(columns=self.columns)
        self.current_path = None

    def load_excel(self, file_path: str) -> bool:
        try:
            file = Path(file_path)
            if not file.exists():
                print(f"Arquivo não encontrado: {file_path}")
                return False

            if file.stat().st_size > 10_000_000:
                chunks = pd.read_excel(file_path, chunksize=5000)
                self.df = pd.concat(chunks, ignore_index=True)
            else:
                self.df = pd.read_excel(file_path)

            # Garante as três colunas e ordem correta
            for col in self.columns:
                if col not in self.df.columns:
                    self.df[col] = ""
            self.df = self.df[self.columns]
            self._preprocess_data()
            self.current_path = file_path
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def save_excel(self, file_path: str = None) -> bool:
        path = file_path or self.current_path
        if not path:
            print("Nenhum caminho de arquivo especificado para salvar.")
            return False

        try:
            self.df.to_excel(path, index=False)
            self.current_path = path
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return False

    def _preprocess_data(self):
        """Garante tipos de dados consistentes e remove linhas inválidas"""
        # Garante que as colunas existem antes de operar
        for col in self.columns:
            if col not in self.df.columns:
                self.df[col] = ""
        # Normaliza tipos
        self.df['RM'] = pd.to_numeric(self.df['RM'], errors='coerce').astype('Int64')
        self.df['Nome do(a) Aluno(a)'] = self.df['Nome do(a) Aluno(a)'].astype(str)
        self.df['Sobrenome'] = self.df['Sobrenome'].astype(str)
        # Remove linhas sem nome ou RM
        self.df = self.df.dropna(subset=['Nome do(a) Aluno(a)', 'RM'])