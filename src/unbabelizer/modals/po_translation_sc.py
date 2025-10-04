import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Tuple, overload

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import HorizontalGroup, ScrollableContainer
from textual.screen import ModalScreen
from textual.suggester import SuggestFromList
from textual.validation import Regex
from textual.widgets import Footer, Header, Input, ProgressBar, Select, Switch
from textual.worker_manager import WorkerManager

from ..log import Logger
from ..types.po_file.handler import POFileHandler
from ..types.po_file.tag import POFileEntryTag
from ..types.translation_service.config import TranslationServiceConfig
from ..types.translation_service.services import TranslationServices
from ..utils import apply_styles, correct_translation, handle_exception, wait_for_element, write_new_tcomment

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class Translator(ModalScreen[None], POFileHandler):
    """A modal screen for translating PO files using Google Translate."""

    BINDINGS = [
        Binding(key="t", action="translate", description=_("Translate"), show=True),
        Binding(key="q", action="quit", description=_("Quit"), show=True),
        Binding(key="o", action="toggle_override", description=_("Toggle Override Existing"), show=True),
        Binding(key="f", action="toggle_fuzzy", description=_("Toggle Fuzzy New Translations"), show=True),
        Binding(key="c", action="cancel", description=_("Cancel translation task"), show=True),
    ]

    def __init__(self, po_path: Path, translation_config: TranslationServiceConfig):
        """Initialize the Translator modal.

        Args:
            po_path (Path): Path to the PO file to be translated.
            translation_service (TranslationServices): The translation service to use.
            config (TranslationServiceConfig): Configuration for the translation service.
        """
        ModalScreen.__init__(self)  # pyright: ignore[reportUnknownMemberType]

        self._translating = False
        self._translation_config = translation_config

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

    @property
    def workers(self) -> WorkerManager:
        """Return the application's worker manager."""
        return getattr(
            self.app,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            "workers",
        )  # pyright: ignore[reportUnknownMemberType]

    def compose_proxies(self) -> ComposeResult:
        """Compose the proxy input fields."""
        yield HorizontalGroup(
            apply_styles(
                Input(
                    placeholder=_("HTTP Proxy"),
                    value=((self._translation_config.get("proxies") or {}).get("http", "")),
                    name="proxy_http",
                    suggester=SuggestFromList(["http://"]),
                ),
                width="1fr",
            ),
            apply_styles(
                Input(
                    placeholder=_("HTTPS Proxy"),
                    value=((self._translation_config.get("proxies") or {}).get("https", "")),
                    name="proxy_https",
                    suggester=SuggestFromList(["https://"]),
                ),
                width="1fr",
            ),
        )

    def compose_model(self) -> ComposeResult:
        """Compose the model input field if supported."""
        yield Input(
            placeholder=_("Model"),
            value=self._translation_config.get("model") or "",
            name="model",
        )

    def compose_region(self) -> ComposeResult:
        """Compose the region input field if supported."""
        yield Input(
            placeholder=_("Region"),
            value=self._translation_config.get("region") or "",
            name="region",
        )

    def compose_api_key(self) -> ComposeResult:
        """Compose the API key input field if needed."""
        yield HorizontalGroup(
            apply_styles(
                Input(
                    placeholder=_("API Key"),
                    value=self._translation_config.get("api_key") or "",
                    password=True,
                    name="api_key",
                ),
                width="2fr",
            ),
            apply_styles(
                Input(
                    placeholder=_('API Key Type ("free" or "paid")'),
                    value=self._translation_config.get("api_key_type") or "",
                    name="api_key_type",
                    suggester=SuggestFromList(["free", "paid"]),
                    validators=(Regex(r"^(free|paid)$", flags=0, failure_description=_("Must be 'free' or 'paid'")),),
                    validate_on=("submitted", "changed"),
                ),
                width="1fr",
            ),
        )

    def compose(self) -> ComposeResult:
        """Compose the UI elements for the modal."""
        yield Header()

        def compose_switches() -> ComposeResult:

            yield HorizontalGroup(
                apply_styles(
                    Input(value=_("Override existing translations:"), disabled=True), width="2fr", vertical="top"
                ),
                apply_styles(
                    Switch(
                        id="override_translations",
                        value=self._translation_config["presets"].get("override_existing_translations") or False,
                    ),
                    width="1fr",
                    vertical="top",
                ),
            )

            yield HorizontalGroup(
                apply_styles(
                    Input(
                        value=_("Fuzzy new translations:        "),
                        disabled=self._translation_config["presets"].get("fuzzy_new_translations") or True,
                    ),
                    width="2fr",
                    vertical="top",
                ),
                apply_styles(Switch(id="fuzzy_translations", value=True), width="1fr", vertical="top"),
            )

        yield apply_styles(
            ScrollableContainer(
                *compose_switches(),
                apply_styles(
                    Select(
                        ((s.translation_service_name, s.value) for s in TranslationServices),
                        value=TranslationServices(
                            TranslationServices.from_service_name(
                                self._translation_config["presets"].get("default_translation_service")
                                or TranslationServices.GOOGLE_TRANSLATE.translation_service_name
                            )
                        ).value,
                        id="translation_service",
                        prompt=_("Select Translation Service"),
                    ),
                    width="1fr",
                    vertical="top",
                ),
                apply_styles(
                    ScrollableContainer(*self.compose_proxies(), id="translator_settings"),
                    width="1fr",
                    vertical="top",
                    height="10fr",
                ),
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

    async def apply_translation_settings(self):
        """Apply the translation settings from the input fields."""
        settings_container = await wait_for_element(lambda: self.query_one("#translator_settings", ScrollableContainer))
        inputs = settings_container.query(Input)
        for input_widget in inputs:
            match input_widget.name:
                case "region" | "model" | "api_key" | "api_key_type":
                    self._translation_config[input_widget.name] = input_widget.value or None

                case "proxy_http" | "proxy_https":
                    proxies = self._translation_config.get("proxies") or {}
                    if input_widget.value:
                        proxies[input_widget.name.removeprefix("proxy_")] = input_widget.value
                    else:
                        proxies.pop(input_widget.name.removeprefix("proxy_"), None)
                    self._translation_config["proxies"] = proxies or None

                case _:
                    pass

        await asyncio.sleep(0)

    def check_action(self, action: str, parameters: Tuple[object, ...]) -> bool | None:
        """Check if an action can be performed."""
        _ = parameters  # Unused
        allowed = not self._translating and action not in ("cancel",) or self._translating and action in ("cancel",)
        self.logger.debug(
            "Action check",
            extra={"context": "Translator.check_action", "action": action, "allowed": allowed},
        )
        return allowed

    async def on_select_changed(self, event: Select.Changed):
        """Handle changes in the translation service selection."""
        if self._translating:
            self.logger.warning(
                "Translation service change ignored during active translation",
                extra={"context": "Translator.on_select_changed"},
            )
            return

        if event.value is Select.BLANK:
            self.logger.warning(
                "Blank translation service selected, ignoring", extra={"context": "Translator.on_select_changed"}
            )
            return

        settings_container = await wait_for_element(lambda: self.query_one("#translator_settings", ScrollableContainer))
        selected_service = TranslationServices(event.value).translation_service_protocol
        await settings_container.remove_children()
        if selected_service.needs_api_key():
            await settings_container.mount_all(self.compose_api_key())
        if selected_service.supports_model():
            await settings_container.mount_all(self.compose_model())
        if selected_service.supports_region():
            await settings_container.mount_all(self.compose_region())
        if selected_service.supports_proxies():
            await settings_container.mount_all(self.compose_proxies())

        self.logger.info(
            "Translation service changed",
            extra={"context": "Translator.on_select_changed", "service": event.value},
        )
        await asyncio.sleep(0)

    async def toggle_checkbox(self, checkbox_id: str):
        """Toggle a checkbox by its ID."""
        if self._translating:
            self.logger.warning(
                f"{checkbox_id} toggle ignored during active translation",
                extra={"context": f"Translator.action_toggle_{checkbox_id}"},
            )
            return

        self.logger.debug(f"Toggling {checkbox_id}", extra={"context": f"Translator.action_toggle_{checkbox_id}"})
        checkbox = await wait_for_element(lambda: self.query_one(f"#{checkbox_id}", Switch))
        checkbox.value = not checkbox.value
        self.logger.info(
            f"{checkbox_id} set to",
            extra={"value": checkbox.value, "context": f"Translator.action_toggle_{checkbox_id}"},
        )

    async def action_toggle_fuzzy(self):
        """Toggle the fuzzy new translations checkbox."""
        await self.toggle_checkbox("fuzzy_translations")

    async def action_toggle_override(self):
        """Toggle the override existing translations checkbox."""
        await self.toggle_checkbox("override_translations")

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

    async def action_cancel(self):
        """Cancel the ongoing translation process."""

        self.logger.info(
            "Cancelling translation process",
            extra={"context": "Translator.action_cancel", "translating": self._translating},
        )
        canceled = self.workers.cancel_group(  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            self, "translation"
        )
        self._translating = not canceled
        if canceled:
            self.notify(
                _("Translation process cancelled."),
                timeout=5,
                title=_("❌ Translation Cancelled"),
            )
            self.dismiss()
            self.logger.info(
                "Translation process cancelled and modal dismissed",
                extra={
                    "context": "Translator.action_cancel",
                    "canceled_workers": canceled,  # pyright: ignore[reportUnknownArgumentType]
                },
            )

        self.logger.info(
            "Translation process cancellation attempted",
            extra={
                "context": "Translator.action_cancel",
                "canceled_workers": canceled,  # pyright: ignore[reportUnknownArgumentType]
            },
        )

    async def translate_pofile(self):
        """Translate the PO file using Google Translate."""
        self.logger.info("Translating PO file...", extra={"context": "Translator.translate_po"})

        self._translating = True
        self.refresh_bindings()
        progressbar = await wait_for_element(lambda: self.query_one(ProgressBar))
        override_existing = (await wait_for_element(lambda: self.query_one("#override_translations", Switch))).value
        mark_as_fuzzy = (await wait_for_element(lambda: self.query_one("#fuzzy_translations", Switch))).value
        selected_value = (await wait_for_element(self.query_one, selector=Select)).value

        selected_service = (
            TranslationServices(selected_value)
            if selected_value is not Select.BLANK
            else TranslationServices.GOOGLE_TRANSLATE
        )
        await self.apply_translation_settings()
        self.logger.info(
            "Using translation service",
            extra={
                "context": "Translator.translate_po",
                "service": selected_service.value,
                "config": self._translation_config,
            },
        )
        with handle_exception(self, self.logger):
            translator = selected_service.translation_service_protocol(self._translation_config)  # type: ignore[reportArgumentType]

            self.notify(
                _("Translating PO file... This may take a while depending on the file size."),
                timeout=5,
                title=_("⏳ Translation Started"),
            )

            for (
                idx,
                entry,  # pyright: ignore[reportUnknownVariableType]
            ) in enumerate(self.pofile):
                changed = False
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
                                    )
                                ),
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
                                "flags": entry.flags,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                "context": "Translator.translate_po",
                            },
                        )
                        self.pofile[idx] = entry
                        changed = True
                    progressbar.advance(2)
                    await asyncio.sleep(0)

                elif entry.msgid:  # pyright: ignore[reportUnknownMemberType]
                    if override_existing or not entry.msgstr:  # pyright: ignore[reportUnknownMemberType]
                        entry.msgstr = correct_translation(
                            entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                            (
                                await translator.translate(  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType, reportArgumentType]
                                    entry.msgid,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                                )
                            ),
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
                        changed = True
                    progressbar.advance(1)
                    await asyncio.sleep(0)

                if changed:
                    write_new_tcomment(
                        entry,
                        " [Translated with {translation_service} on {{timestamp}}]".format(
                            translation_service=selected_service.value,
                        ),
                    )
                    (POFileEntryTag.FUZZY if mark_as_fuzzy else POFileEntryTag.UNCONFIRMED).apply(entry)

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
