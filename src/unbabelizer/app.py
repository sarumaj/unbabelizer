import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Tuple, overload

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Header, ProgressBar, SelectionList, Static, TabbedContent, TabPane

from .config import Config
from .log import Logger
from .modals.confirm_inevitable import ConfirmInevitable
from .modals.po_review_sc import POReviewScreen
from .modals.po_translation_sc import Translator
from .translation import get_display_name_for_lang_code
from .types.subcommand import SubCommands
from .utils import apply_styles, handle_exception, run_babel_cmd, wait_for_element

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class UnbabelizerApp(App[None]):
    """The main application class for unbabelizer."""

    BINDINGS = [
        Binding(key="r", action="run_workflow", description=_("Run Workflow"), show=True),
        Binding(key="q", action="quit", description=_("Quit"), show=True),
        Binding(key="c", action="clear", description=_("Clear translation files"), show=True),
    ]

    def __init__(self, config: Config, logger: Logger | None):
        """Initialize the unbabelizerApp with the given configuration.

        Args:
            config (Config): The configuration for the application.
        """
        super().__init__()
        self.get_theme_variable_defaults()
        self._app_logger = logger or Logger()
        self._config = config
        self._config.locale_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._current_lang_idx = 0
        self._workflow_running = False
        self.logger.debug(
            "unbabelizerApp initialized with config:", extra={"config": self._config, "context": "unbabelizerApp.init"}
        )

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return self._app_logger

    @property
    def potfile_path(self) -> Path:
        """Path to the .pot file."""
        return self._config.potfile_path

    @property
    def pofile_path(self) -> Path:
        """Path to the .po file for the target language."""
        return self._config.get_pofile_path(self._current_lang_idx)

    def compose(self) -> ComposeResult:
        """Compose the UI elements for the main application."""
        yield Header()
        with TabbedContent(initial=""):

            for lang in self._config.dest_lang:
                with TabPane(get_display_name_for_lang_code(lang), name=lang):
                    yield apply_styles(
                        ScrollableContainer(
                            Static(_("Translation Workflow")),
                            SelectionList(
                                (
                                    SubCommands.EXTRACT_UPDATE.command_description,
                                    SubCommands.EXTRACT_UPDATE.command_name,
                                    self._config.is_workflow_action_enabled(SubCommands.EXTRACT_UPDATE, True),
                                ),
                                (
                                    SubCommands.TRANSLATE.command_description,
                                    SubCommands.TRANSLATE.command_name,
                                    self._config.is_workflow_action_enabled(SubCommands.TRANSLATE, False),
                                ),
                                (
                                    SubCommands.REVIEW.command_description,
                                    SubCommands.REVIEW.command_name,
                                    self._config.is_workflow_action_enabled(SubCommands.REVIEW, True),
                                ),
                                (
                                    SubCommands.COMPILE.command_description,
                                    SubCommands.COMPILE.command_name,
                                    self._config.is_workflow_action_enabled(SubCommands.COMPILE, True),
                                ),
                                id=f"workflow_selection_list_{lang}",
                            ),
                            apply_styles(
                                ProgressBar(total=100, show_eta=True, show_percentage=True, id=f"progress_bar_{lang}"),
                                vertical="bottom",
                                width="1fr",
                                height="1fr",
                            ),
                        ),
                        vertical="top",
                        width="1fr",
                        height="1fr",
                    )
        yield Footer()

    async def on_mount(self):
        """Handle the mount event for the application."""
        (
            await wait_for_element(
                self.query_one,
                selector=f"#workflow_selection_list_{self._config.dest_lang[self._current_lang_idx]}",
                expect_type=SelectionList,
            )
        ).focus()

    async def on_tabbed_content_tab_activated(self, message: TabbedContent.TabActivated):
        """Handle tab activation events to switch target languages."""
        if (
            not message.tabbed_content.active_pane
            or message.tabbed_content.active_pane.name not in self._config.dest_lang
        ):
            self.logger.warning(
                "Activated tab not in configured destination languages",
                extra={"activated_tab": message.tab.id, "context": "unbabelizerApp.on_tabbed_content_tab_activated"},
            )
            return

        self._current_lang_idx = self._config.dest_lang.index(f"{message.tabbed_content.active_pane.name}")
        self.logger.info(
            "Target language changed",
            extra={
                "new_language": self._config.dest_lang[self._current_lang_idx],
                "context": "unbabelizerApp.on_tabbed_content_tab_activated",
            },
        )

    def check_action(self, action: str, parameters: Tuple[object, ...]) -> bool | None:
        """Check if an action can be performed."""
        _ = (action, parameters)  # Unused
        return not self._workflow_running

    async def action_clear(self):
        """Clear all .po and .mo files in the locale directory."""

        def callback(result: Any):
            if result is not True:
                return

            self.logger.info("Clearing translation files...", extra={"context": "unbabelizerApp.clear"})
            with handle_exception(self, self.logger):
                for path in self._config.locale_dir.rglob("*"):
                    if path.is_file():
                        self.logger.debug("Removing file", extra={"path": path, "context": "unbabelizerApp.clear"})
                        path.unlink()

                for path in self._config.locale_dir.rglob("*"):
                    if path.is_dir() and not any(path.iterdir()):
                        self.logger.debug(
                            "Removing empty directory", extra={"path": path, "context": "unbabelizerApp.clear"}
                        )
                        path.rmdir()

                self.notify(_("All translation files cleared."), timeout=3, title=_("✅ Success"))
                self.logger.info("Translation files cleared.", extra={"context": "unbabelizerApp.clear"})

        await self.push_screen(ConfirmInevitable(), callback=callback)

    async def action_run_workflow(self):
        """Run the selected workflow actions."""
        self.logger.info("Running workflow actions...", extra={"context": "unbabelizerApp.run_workflow"})
        selection_list = await wait_for_element(
            self.query_one,
            selector=f"#workflow_selection_list_{self._config.dest_lang[self._current_lang_idx]}",
            expect_type=SelectionList,
        )
        selections = [f"{option}" for option in selection_list.selected]
        if not selections:
            self.logger.warning("No actions selected to run", extra={"context": "unbabelizerApp.run_workflow"})
            self.notify(_("No actions selected to run."), timeout=3, title=_("⚠️ Warning"))
            return

        self._workflow_running = True
        self.logger.debug(
            "Selected actions:", extra={"selections": selections, "context": "unbabelizerApp.run_workflow"}
        )
        progress_bar = await wait_for_element(
            self.query_one,
            selector=f"#progress_bar_{self._config.dest_lang[self._current_lang_idx]}",
            expect_type=ProgressBar,
        )
        progress_bar.update(total=100, progress=0)
        actions = {
            SubCommands.EXTRACT_UPDATE.value.name: self.flow_extract_and_update,
            SubCommands.TRANSLATE.value.name: self.flow_translate_pofile,
            SubCommands.REVIEW.value.name: self.flow_review_pofile,
            SubCommands.COMPILE.value.name: self.flow_compile_translations,
        }
        for action in actions:
            if action in selections:
                self.logger.info(f"Starting action: {action}", extra={"context": "unbabelizerApp.run_workflow"})
                actions[action]()
                progress_bar.advance(100 // (len(selections) or 1))

        progress_bar.update(total=100, progress=100)
        self._workflow_running = False

    async def action_quit(self):
        """Quit the application."""
        self.logger.info("Quitting application...", extra={"context": "unbabelizerApp.quit"})
        self.exit()

    @staticmethod
    def run_action_extract_and_update(
        logger: Logger, config: Config, current_lang_idx: int, potfile_path: Path, pofile_path: Path
    ):
        """Extract messages and update or initiate .po files."""
        logger.info(
            "Extracting and updating translations...", extra={"context": "unbabelizerApp.flow_extract_and_update"}
        )

        # Extraction (overwrite existing .pot file)
        mapping_file = config.locale_dir / "babel_mapping.txt"
        logger.debug(
            "Creating temporary Babel mapping file",
            extra={"path": mapping_file, "context": "unbabelizerApp.flow_extract_and_update"},
        )
        mapping_file.touch()
        mapping_file.write_text(config.mapping_file.strip() + "\n")
        logger.debug(
            "Babel mapping file content:",
            extra={"content": mapping_file.read_text(), "context": "unbabelizerApp.flow_extract_and_update"},
        )

        logger.debug("Running Babel extract command", extra={"context": "unbabelizerApp.flow_extract_and_update"})

        run_babel_cmd(
            ["extract"]
            + ["--project", config.title]
            + ["--version", config.version]
            + ["--copyright-holder", config.author]
            + ["--last-translator", config.email]
            + ["--sort-output"]
            + ["-F", str(mapping_file.resolve())]
            + ["-o", str(potfile_path)]
            + [f"--keywords={kw}" for kw in config.keywords]
            + (
                ["--ignore-dirs", *(ex for ex in config.exclude_patterns)]
                + ["--input-paths", *(str(i.resolve()) for i in config.input_paths)]
                if config.exclude_patterns
                else [str(i.resolve()) for i in config.input_paths]
            )
        )
        mapping_file.unlink()

        if pofile_path.exists():
            logger.debug(
                "Updating existing .po file",
                extra={"path": pofile_path, "context": "unbabelizerApp.flow_extract_and_update"},
            )
            # Update existing .po file
            run_babel_cmd(
                ["update"]
                + ["-D", config.domain]
                + ["-i", str(potfile_path)]
                + ["-d", str(config.locale_dir)]
                + ["-l", config.dest_lang[current_lang_idx]]
                + ["-w", str(config.line_width)]
                + ["--init-missing"]
                + ["--ignore-pot-creation-date"]
            )
        else:
            logger.debug(
                "Creating new .po file",
                extra={"path": pofile_path, "context": "unbabelizerApp.flow_extract_and_update"},
            )
            # Initialize new .po file
            run_babel_cmd(
                ["init"]
                + ["-i", str(potfile_path)]
                + ["-d", str(config.locale_dir)]
                + ["-l", config.dest_lang[current_lang_idx]]
                + ["-w", str(config.line_width)]
                + ["-D", config.domain]
            )
        logger.info(
            "Extraction and update completed.",
            extra={
                "pot_path": potfile_path,
                "po_path": pofile_path,
                "context": "unbabelizerApp.flow_extract_and_update",
            },
        )

    @staticmethod
    def run_action_compile_translations(logger: Logger, config: Config):
        """Compile .po files into .mo files."""
        logger.info("Compiling translations...", extra={"context": "unbabelizerApp.flow_compile_translations"})
        run_babel_cmd(["compile"] + ["-D", config.domain] + ["-d", str(config.locale_dir)])
        logger.info("Compilation completed.", extra={"context": "unbabelizerApp.flow_compile_translations"})

    @work(group="main")
    async def flow_extract_and_update(self):
        """Extract messages and update or initiate .po files."""
        async with self._lock:
            with handle_exception(self, self.logger):
                self.run_action_extract_and_update(
                    self.logger,
                    self._config,
                    self._current_lang_idx,
                    self.potfile_path,
                    self.pofile_path,
                )
                self.notify(_("Extraction and update completed."), timeout=3, title=_("✅ Success"))

    @work(group="main")
    async def flow_compile_translations(self):
        """Compile .po files into .mo files."""
        async with self._lock:
            with handle_exception(self, self.logger):
                self.run_action_compile_translations(self.logger, self._config)

    @work(group="main")
    async def flow_translate_pofile(self):
        """Translate the .po file using Google Translate."""
        self.logger.info("Pushing translation screen", extra={"context": "unbabelizerApp.flow_translate_po"})
        await self._lock.acquire()
        await self.push_screen(
            Translator(
                self.pofile_path,
                self._config.get_translation_config(self._current_lang_idx),  # pyright: ignore[reportArgumentType]
            ),
            callback=lambda _: self._lock.release(),
        )
        self.logger.info("Translation screen pushed", extra={"context": "unbabelizerApp.flow_translate_po"})

    @work(group="main")
    async def flow_review_pofile(self):
        """Review and edit the .po file."""
        self.logger.info("Pushing PO review screen", extra={"context": "unbabelizerApp.flow_review_po"})
        await self._lock.acquire()
        await self.push_screen(
            POReviewScreen(self.pofile_path),
            callback=lambda _: self._lock.release(),
        )
        self.logger.info("PO review screen dismissed", extra={"context": "unbabelizerApp.flow_review_po"})
