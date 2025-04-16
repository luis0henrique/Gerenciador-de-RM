import os
import json
from typing import Dict, Any, List, Optional

class ConfigManager:
    DEFAULT_CONFIG = {
        "recent_files": [],
        "last_path": None,
        "theme": "light",
        "max_recent_files": 5
    }

    def __init__(self, config_file: str = "resources/config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carrega o arquivo de configuração ou cria um novo com valores padrão"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Garante que todos os campos padrão existam
                    for key, value in self.DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erro ao carregar config: {e}")
                # Se o arquivo estiver corrompido, cria um novo
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self) -> Dict[str, Any]:
        """Cria um novo arquivo de configuração com valores padrão"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=4)
        return self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Salva a configuração atual no arquivo"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")

    # Métodos para recent_files
    def get_recent_files(self) -> List[str]:
        """Retorna a lista de arquivos recentes válidos"""
        recent_files = self.config.get("recent_files", [])
        # Filtra apenas arquivos existentes
        valid_files = [fp for fp in recent_files if fp and os.path.exists(fp)]

        # Se houve remoção de arquivos inválidos, atualiza a lista
        if len(valid_files) != len(recent_files):
            self.config["recent_files"] = valid_files
            self.save_config()

        return valid_files

    def add_recent_file(self, file_path: str):
        """Adiciona um arquivo à lista de recentes"""
        if not file_path or not os.path.exists(file_path):
            return

        recent_files = self.get_recent_files()
        max_files = self.config.get("max_recent_files", 5)

        if file_path in recent_files:
            recent_files.remove(file_path)

        recent_files.insert(0, file_path)
        recent_files = recent_files[:max_files]

        self.config["recent_files"] = recent_files
        self.save_config()

    # Métodos para last_path
    def get_last_path(self) -> Optional[str]:
        """Retorna o último caminho acessado"""
        path = self.config.get("last_path")
        return path if path and os.path.exists(path) else None

    def set_last_path(self, file_path: str):
        """Define o último caminho acessado"""
        if file_path:
            self.config["last_path"] = file_path
            self.save_config()

    # Métodos para theme
    def get_theme(self) -> str:
        """Retorna o tema atual"""
        return self.config.get("theme", "light")

    def set_theme(self, theme_name: str):
        """Define o tema atual"""
        if theme_name in ("light", "dark"):
            self.config["theme"] = theme_name
            self.save_config()