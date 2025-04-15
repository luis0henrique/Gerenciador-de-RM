import pandas as pd
from pathlib import Path

class ExcelManager:
    def __init__(self):
        self.df = pd.DataFrame(columns=['Nome do(a) Aluno(a)', 'RM'])
        self.current_path = None

    def load_excel(self, file_path: str) -> bool:
        try:
            if Path(file_path).stat().st_size > 10_000_000:
                chunks = pd.read_excel(file_path, chunksize=5000)
                self.df = pd.concat(chunks, ignore_index=True)
            else:
                self.df = pd.read_excel(file_path)

            self._preprocess_data()
            self.current_path = file_path
            return True
        except Exception as e:
            print(f"Erro ao carregar arquivo: {e}")
            return False

    def save_excel(self, file_path: str = None) -> bool:
        path = file_path or self.current_path
        if not path:
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
        self.df['RM'] = pd.to_numeric(self.df['RM'], errors='coerce').astype('Int64')
        self.df['Nome do(a) Aluno(a)'] = self.df['Nome do(a) Aluno(a)'].astype(str)
        self.df = self.df.dropna(subset=['Nome do(a) Aluno(a)', 'RM'])