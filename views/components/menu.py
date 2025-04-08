import os
from PyQt5.QtWidgets import QApplication, QAction, QMenu, QActionGroup
from utils.styles import get_stylesheet, get_dark_stylesheet

class MenuManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_theme = 'light'

    def create_menu_bar(self):
        """Cria toda a barra de menus"""
        menu_bar = self.main_window.menuBar()
        menu_bar.clear()

        # Menus principais
        self._setup_file_menu(menu_bar.addMenu("Arquivo"))
        self._setup_theme_menu(menu_bar.addMenu("Tema"))

    def _setup_file_menu(self, file_menu):
        open_action = QAction("Abrir", self.main_window)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.main_window.file_ops.load_file)

        save_action = QAction("Salvar", self.main_window)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.main_window.file_ops.save_file)

        save_as_action = QAction("Salvar Como...", self.main_window)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.main_window.file_ops.save_file_as)

        exit_action = QAction("Sair", self.main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.main_window.close)

        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addAction(save_as_action)

        # Menu Recentes
        self.recent_menu = QMenu("Abrir Recente", self.main_window)
        self.recent_menu.aboutToShow.connect(self._update_recent_menu)

        file_menu.addMenu(self.recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def _setup_theme_menu(self, theme_menu):
        self.theme_action_group = QActionGroup(self.main_window)

        themes = [
            ("Claro", 'light', get_stylesheet),
            ("Escuro", 'dark', get_dark_stylesheet)
        ]

        for name, theme, stylesheet_func in themes:
            action = QAction(name, self.main_window)
            action.setCheckable(True)
            action.triggered.connect(lambda _, t=theme: self._change_theme(t))
            self.theme_action_group.addAction(action)
            theme_menu.addAction(action)

        self._update_theme_menu()

    def _change_theme(self, theme_name):
        from utils.styles import apply_theme
        self.current_theme = apply_theme(QApplication.instance(), theme_name)
        self._update_theme_menu()

    def _update_theme_menu(self):
        if hasattr(self, 'theme_action_group'):
            for action in self.theme_action_group.actions():
                action.setChecked(
                    (action.text() == "Claro" and self.current_theme == 'light') or
                    (action.text() == "Escuro" and self.current_theme == 'dark')
                )

    def _update_recent_menu(self):
        """Atualiza o menu dinamicamente quando é aberto"""
        self.recent_menu.clear()

        recent_files = self.main_window.file_ops.get_recent_files()

        if not recent_files:
            action = self.recent_menu.addAction("Nenhum arquivo recente")
            action.setEnabled(False)
            return

        for i, file_path in enumerate(recent_files):
            action = self.recent_menu.addAction(f"{i+1}. {os.path.basename(file_path)}")
            action.triggered.connect(lambda checked, fp=file_path: self._load_recent_file(fp))

    def _load_recent_file(self, file_path):
        """Carrega um arquivo recente"""
        success = self.main_window.file_ops.load_recent_file(file_path)
        if not success:
            # Se falhar, remove da lista e atualiza o menu
            self.main_window.file_ops.recent_files.remove(file_path)
            self.main_window.file_ops._save_recent_files()
            self._update_recent_menu()
