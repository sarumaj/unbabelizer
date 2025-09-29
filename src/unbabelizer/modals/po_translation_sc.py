import asyncio
from gettext import gettext as _
from pathlib import Path

from googletrans import Translator as GoogleTranslator
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Checkbox, Footer, Header, ProgressBar
from textual.widgets import Static as Placeholder

from ..log import Logger
from ..types import POFileHandler
from ..utils import NotifyException, apply_styles, correct_translation, wait_for_element


class Translator(ModalScreen[None], POFileHandler):
    """A modal screen for translating PO files using Google Translate."""

    BINDINGS = [
        Binding(key="t", action="translate", description=_("Translate"), show=True),
        Binding(key="q", action="quit", description=_("Quit"), show=True),
        Binding(key="o", action="toggle_override", description=_("Toggle Override Existing"), show=True),
    ]

    def __init__(self, po_path: Path, src_lang: str, target_lang: str):
        """Initialize the Translator modal.

        Args:
            po_path (Path): Path to the PO file to be translated.
            src_lang (str): Source language code.
            target_lang (str): Target language code.
        """
        ModalScreen.__init__(self)  # pyright: ignore[reportUnknownMemberType]

        self._src_lang = src_lang
        self._target_lang = target_lang
        self._translating = False

        self.logger.info(
            "Loading PO file for translation...",
            extra={"context": "Translator.init", "path": str(po_path)},
        )
        POFileHandler.__init__(self, po_path)
        self.logger.info(
            "PO file loaded",
            extra={
                "context": "Translator.init",
                "path": str(self.pofile_path),
                "entries": len(list(self.pofile)),  # pyright: ignore[reportUnknownArgumentType, reportArgumentType]
            },
        )

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return getattr(
            self.app,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            "logger",
        )

    def compose(self) -> ComposeResult:
        """Compose the UI elements for the modal."""
        yield Header()
        yield apply_styles(
            Container(
                apply_styles(Checkbox(label=_("Override existing translations"), value=False), width="1fr"),
                apply_styles(Placeholder(), height="1fr"),
                apply_styles(
                    ProgressBar(
                        total=sum(
                            1 + (1 if e.msgid_plural else 0)  # pyright: ignore[reportUnknownMemberType]
                            for e in self.pofile  # pyright: ignore[reportUnknownVariableType]
                        )
                    ),
                    vertical="bottom",
                    width="1fr",
                ),
            ),
            vertical="top",
            width="1fr",
        )
        yield Footer()

    async def action_toggle_override(self):
        """Toggle the override existing translations checkbox."""
        self.logger.debug(
            "Toggling override existing translations", extra={"context": "Translator.action_toggle_override"}
        )
        checkbox = await wait_for_element(lambda: self.query_one(Checkbox))
        checkbox.value = not checkbox.value
        self.logger.info(
            "Override existing translations set to",
            extra={"value": checkbox.value, "context": "Translator.action_toggle_override"},
        )

    async def action_quit(self):
        """Quit the modal."""
        self.logger.info("Quitting Translator modal", extra={"context": "Translator.action_quit"})
        self.dismiss()
        self.logger.info("Translator modal dismissed", extra={"context": "Translator.action_quit"})

    async def action_translate(self):
        """Start the translation process."""
        self.logger.info("Starting translation process", extra={"context": "Translator.action_translate"})
        self.run_worker(self.translate_pofile, group="translation")
        self.logger.info("Translation process started", extra={"context": "Translator.action_translate"})

    async def translate_pofile(self):
        """Translate the PO file using Google Translate."""
        self.logger.info("Translating PO file...", extra={"context": "Translator.translate_po"})

        self._translating = True
        progressbar = await wait_for_element(lambda: self.query_one(ProgressBar))
        override_existing = (await wait_for_element(lambda: self.query_one(Checkbox))).value

        self.notify(
            _("Translating PO file... This may take a while depending on the file size."),
            timeout=5,
            title=_("⏳ Translation Started"),
        )
        with NotifyException(self):
            translator = GoogleTranslator()
            for (
                idx,
                entry,  # pyright: ignore[reportUnknownVariableType]
            ) in enumerate(self.pofile):
                if entry.msgid_plural:  # pyright: ignore[reportUnknownMemberType]
                    if override_existing or not all(
                        entry.msgstr_plural.values()  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                    ):
                        entry.msgstr_plural = {
                            index: correct_translation(
                                elem,  # type: ignore[reportUnknownArgumentType]
                                (
                                    await translator.translate(
                                        elem,  # type: ignore[reportUnknownArgumentType]
                                        src=self._src_lang,
                                        dest=self._target_lang,
                                    )
                                ).text,
                            )
                            for index, elem in enumerate(  # pyright: ignore[reportUnknownVariableType]
                                (
                                    entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                    entry.msgid_plural,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                )
                            )
                        }
                        self.logger.debug(
                            "Translated plural entry",
                            extra={
                                "msgid": entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                "msgid_plural": entry.msgid_plural,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                "context": "Translator.translate_po",
                            },
                        )
                        self.pofile[idx] = entry
                    progressbar.advance(2)
                    await asyncio.sleep(0)

                elif entry.msgid:  # pyright: ignore[reportUnknownMemberType]
                    if override_existing or not entry.msgstr:  # pyright: ignore[reportUnknownMemberType]
                        entry.msgstr = correct_translation(
                            entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                            (
                                await translator.translate(  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportArgumentType]
                                    entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                    src=self._src_lang,
                                    dest=self._target_lang,
                                )
                            ).text,
                        )
                        self.logger.debug(
                            "Translated singular entry",
                            extra={
                                "msgid": entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                "msgstr": entry.msgstr,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                "context": "Translator.translate_po",
                            },
                        )
                        self.pofile[idx] = entry
                    progressbar.advance(1)
                    await asyncio.sleep(0)

            self.logger.info(
                "Translation completed, saving PO file...",
                extra={"context": "Translator.translate_po", "path": str(self.pofile_path)},
            )
            self.pofile.save(str(self.pofile_path))  # pyright: ignore[reportUnknownMemberType]
            self._translating = False
            self.dismiss()
            self.logger.info(
                "PO file saved and modal dismissed",
                extra={"context": "Translator.translate_po", "path": str(self.pofile_path)},
            )
            self.notify(_("Translation completed and PO file saved."), timeout=5, title=_("⌛ Translation Completed"))
