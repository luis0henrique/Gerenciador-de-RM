import logging
from PyQt5.QtCore import Qt
from utils.helpers import remove_acentos

# Minimum Levenshtein similarity score to consider a name a match (0-1).
# 0.75 = 75% similar. Adjust up for stricter, down for more lenient results.
FUZZY_THRESHOLD = 0.75

# Minimum number of characters typed before fuzzy search activates.
# Avoids noisy results for very short queries.
FUZZY_MIN_LENGTH = 4


class SearchManager:
    def __init__(self, excel_manager, table_manager, message_handler):
        self.logger = logging.getLogger(__name__)
        self.excel_manager = excel_manager
        self.table_manager = table_manager
        self.message_handler = message_handler

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_student(self, search_term):
        """Executa a busca por aluno baseada no termo fornecido.

        A busca é realizada em três camadas progressivas:
          1. Substring exata (normalizada/sem acentos) — rápida, sem custo.
          2. Todos os tokens do termo estão presentes no nome (ordem livre).
          3. Fuzzy por Levenshtein token-a-token (captura typos e junções como
             'Joaoda' ao buscar 'Joao da').
        """
        if not hasattr(self.excel_manager, 'df') or self.excel_manager.df.empty:
            self.logger.warning("Tentativa de busca sem dados carregados.")
            return False

        if not search_term.strip():
            self.restore_full_list()
            return True

        normalized_term = remove_acentos(search_term.strip().lower())

        if normalized_term.isdigit():
            result = self._search_by_rm(normalized_term)
            self.message_handler.show_search_results(len(result), by_rm=True)
        else:
            result = self._search_by_name(normalized_term)
            self.message_handler.show_search_results(len(result), by_rm=False)

        if result.empty:
            self.logger.info(f"Nenhum resultado encontrado para: '{search_term}'")
            self.message_handler.show_message("Nenhum aluno encontrado.", "warning")

        result_sorted = result.sort_values('Nome do(a) Aluno(a)')
        self.table_manager.update_table_with_data(result_sorted)
        self.table_manager.table.sortByColumn(1, Qt.AscendingOrder)
        return True

    def restore_full_list(self):
        """Restaura a lista completa de alunos."""
        if hasattr(self.excel_manager, 'df'):
            record_count = len(self.excel_manager.df)
            self.message_handler.show_record_count(record_count)
            self.table_manager.update_table()
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _search_by_rm(self, normalized_term):
        return self.excel_manager.df[
            self.excel_manager.df['RM'].astype(str) == normalized_term
        ]

    def _search_by_name(self, normalized_term):
        """Busca em três camadas progressivas, retornando a união dos resultados."""
        df = self.excel_manager.df

        # Coluna de nomes normalizada (calculada uma única vez)
        names_normalized = df['Nome do(a) Aluno(a)'].apply(
            lambda x: remove_acentos(str(x).lower())
        )

        # --- Camada 1: substring exata ---
        mask_exact = names_normalized.str.contains(normalized_term, regex=False)
        exact_idx = set(df.index[mask_exact])

        # --- Camada 2: todos os tokens presentes no nome (ordem livre) ---
        query_tokens = normalized_term.split()
        token_idx = self._token_match(names_normalized, query_tokens, exclude=exact_idx)

        # --- Camada 3: fuzzy Levenshtein (só ativa para termos suficientemente longos) ---
        if len(normalized_term) >= FUZZY_MIN_LENGTH:
            fuzzy_idx = self._fuzzy_match(
                names_normalized,
                query_tokens,
                exclude=exact_idx | token_idx,
            )
        else:
            fuzzy_idx = set()

        matched_idx = exact_idx | token_idx | fuzzy_idx

        if not matched_idx:
            return df.iloc[0:0]  # DataFrame vazio com as colunas corretas

        return df.loc[sorted(matched_idx)]

    # --- Camada 2 ---

    def _token_match(self, names_normalized, query_tokens, exclude):
        """Retorna índices onde TODOS os tokens da query aparecem no nome."""
        if not query_tokens:
            return set()

        result_idx = set()
        for i, name in names_normalized.items():
            if i in exclude:
                continue
            # Todos os tokens devem estar presentes (substring de qualquer parte do nome)
            if all(tok in name for tok in query_tokens):
                result_idx.add(i)
        return result_idx

    # --- Camada 3 ---

    def _fuzzy_match(self, names_normalized, query_tokens, exclude):
        """
        Fuzzy matching token-a-token usando Levenshtein.

        Estratégia:
          - Para cada nome no DataFrame, divide-o em tokens.
          - Para cada token da query, procura o token do nome com maior
            similaridade (score >= FUZZY_THRESHOLD).
          - O nome é incluído somente se TODOS os tokens da query tiverem
            um par satisfatório no nome.

        Isso captura casos como:
          - "Joao da Silva" vs "Joaoda Silva"  (junção de tokens)
          - "Joao" vs "João"                   (já coberto pela normalização)
          - "Silvo" vs "Silva"                 (typo de 1 caractere)
        """
        try:
            # Tenta reutilizar o matcher do DataManager (já tem cache aquecido)
            from models.data_manager import LevenshteinMatcher
            matcher = LevenshteinMatcher()
        except ImportError:
            self.logger.debug("LevenshteinMatcher não disponível; fuzzy search desativado.")
            return set()

        result_idx = set()

        for i, name in names_normalized.items():
            if i in exclude:
                continue

            name_tokens = name.split()
            if not name_tokens:
                continue

            # Verifica se cada token da query tem correspondência suficiente
            # em algum token do nome (ou em pares de tokens concatenados).
            if self._all_query_tokens_match(matcher, query_tokens, name_tokens):
                result_idx.add(i)

        return result_idx

    def _all_query_tokens_match(self, matcher, query_tokens, name_tokens):
        """
        Retorna True se cada token da query tiver similaridade >= FUZZY_THRESHOLD
        com pelo menos um token do nome (ou com a concatenação de dois tokens
        adjacentes, para capturar casos como 'joaoda' = 'joao' + 'da').
        """
        # Gera candidatos: tokens individuais + pares adjacentes concatenados
        # Ex: ["joaoda", "silva"] → candidatos: "joaoda", "silva", "joaodasilva"
        candidates = list(name_tokens)
        for j in range(len(name_tokens) - 1):
            candidates.append(name_tokens[j] + name_tokens[j + 1])

        for q_tok in query_tokens:
            # Tokens muito curtos (artigos como "da", "de") são ignorados
            # para evitar falsos positivos no fuzzy.
            if len(q_tok) <= 2:
                continue

            best_score = 0.0
            for candidate in candidates:
                if len(candidate) < 2:
                    continue
                score = matcher.similarity_score(q_tok, candidate)
                if score > best_score:
                    best_score = score
                if best_score >= FUZZY_THRESHOLD:
                    break  # Early exit: já encontrou match suficiente

            if best_score < FUZZY_THRESHOLD:
                return False  # Este token da query não teve correspondência

        return True