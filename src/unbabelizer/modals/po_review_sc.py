from fnmatch import fnmatch
from gettext import gettext as _
from pathlib import Path
from typing import Any, Generator, List, Tuple

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.coordinate import Coordinate
from textual.events import Key
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header

from ..log import Logger
from ..types import POFileEntryTag, POFileHandler, TableCell
from ..utils import NotifyException, apply_styles, escape_control_chars, wait_for_element
from .confirm_inevitable import ConfirmInevitable
from .po_edit_sc import POEditScreen


class POReviewScreen(ModalScreen[None], POFileHandler):
    """A modal screen for reviewing and editing PO file translations."""

    BINDINGS = [
        Binding(key="s", action="save", description=_("Save"), show=True),
        Binding(key="e", action="edit", description=_("Edit Selected"), show=True),
        Binding(key="enter", action="edit", description=_("Edit Selected"), show=False),
        Binding(key="f", action="filter", description=_("Filter rows"), show=True),
        Binding(key="q", action="quit", description=_("Quit and Save"), show=True),
        Binding(key="a", action="abort", description=_("Quit without Saving"), show=True),
    ]

    def __init__(self, po_path: Path):
        """Initialize the POReviewScreen modal.

        Args:
            po_path (Path): Path to the PO file to be reviewed.
        """
        ModalScreen.__init__(self)  # pyright: ignore[reportUnknownMemberType]

        self.logger.info(
            "Loading PO file for review...",
            extra={"context": "POReviewScreen.init", "path": str(po_path)},
        )
        POFileHandler.__init__(self, po_path)
        self.logger.info(
            "PO file loaded",
            extra={
                "context": "POReviewScreen.init",
                "path": str(self.pofile_path),
                "entries": len(list(self.pofile)),  # pyright: ignore[reportUnknownArgumentType, reportArgumentType]
            },
        )

        self.entries: List[Tuple[Any, ...]] = []
        for entry in self.pofile:  # pyright: ignore[reportUnknownVariableType]
            if entry.msgid_plural:  # pyright: ignore[reportUnknownMemberType]
                for idx in sorted(  # pyright: ignore[reportUnknownVariableType]
                    entry.msgstr_plural.keys()  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                ):
                    self.entries.append((entry, idx))  # pyright: ignore[reportUnknownArgumentType]
            else:
                self.entries.append((entry, None))  # pyright: ignore[reportUnknownArgumentType]

        self.logger.info(
            "POReviewScreen initialized",
            extra={"context": "POReviewScreen.init", "entries": len(self.entries)},
        )

    @property
    def logger(self) -> Logger:
        """Return the application logger."""
        return getattr(
            self.app,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            "logger",
        )

    def generate_cells(self) -> Generator[TableCell, None, None]:
        """Generate table cells for the PO entries.

        Returns:
            Generator[TableCell, None, None]: A generator of TableCell instances.
        """
        for no, (entry, idx) in enumerate(self.entries):
            if idx is None:
                yield TableCell(
                    f"{no}",
                    "Singular",
                    escape_control_chars(entry.msgid),
                    escape_control_chars(entry.msgstr),
                    POFileEntryTag.fish(entry, POFileEntryTag.UNKNOWN).value,
                )
            else:
                yield TableCell(
                    f"{no}",
                    f"Plural[{idx}]",
                    escape_control_chars(entry.msgid if idx == 0 else entry.msgid_plural),
                    escape_control_chars(entry.msgstr_plural[idx]),
                    POFileEntryTag.fish(entry, POFileEntryTag.UNKNOWN).value,
                )

    def compose(self) -> ComposeResult:
        """Compose the UI elements for the modal."""
        yield Header()
        table = DataTable[str](zebra_stripes=True)
        table.add_columns("", _("Type"), _("MsgId"), _("MsgStr"), _("Tag"))
        for cell in self.generate_cells():
            table.add_row(cell.row_no, cell.type, cell.msgid, cell.msgstr, cell.tag)
        yield apply_styles(ScrollableContainer(table), width="1fr", height="1fr", vertical="top")
        yield Footer()

    async def key_enter(self, event: Key):
        """Handle key events for the modal."""
        event.prevent_default()
        event.stop()
        self.logger.debug(
            "Executing action for key:",
            extra={"action": "edit", "context": "POReviewScreen.key_enter"},
        )
        await self.run_action("edit")

    async def on_mount(self):
        """Focus the data table when the modal is mounted."""
        table = await wait_for_element(self.query_one, selector=DataTable)
        table.focus()
        self.logger.info("DataTable focused on mount", extra={"context": "POReviewScreen.on_mount"})

    def edit_translation_callback(self, result: Any):
        """Edit the translation of the currently selected entry."""
        if not isinstance(result, str):
            self.logger.warning(
                "Edit translation callback received non-string result, ignoring.",
                extra={"result": str(result), "context": "POReviewScreen.edit_translation_callback"},
            )
            return

        self.logger.debug(
            "Editing translation", extra={"new_value": result, "context": "POReviewScreen.edit_translation"}
        )
        table: DataTable[str] = self.query_one(DataTable)  # pyright: ignore[reportUnknownVariableType]
        for label, value in ((_("MsgStr"), escape_control_chars(result)), (_("Tag"), POFileEntryTag.REVIEWED.value)):
            column_index = [f"{column.label}" for column in table.columns.values()].index(label)
            coordinate = Coordinate(table.cursor_row, column_index)
            old_value = table.get_cell_at(coordinate)
            table.update_cell_at(coordinate, value, update_width=True)

            if label == _("MsgStr"):
                self.notify(
                    _("Translation updated.")
                    + "\n"
                    + _('Previous value was: "{old_value}", current value is: "{new_value}".').format(
                        old_value=old_value or _("<empty>"), new_value=result or _("<empty>")
                    ),
                    timeout=2,
                    title=_("✅ Success"),
                )

            self.logger.debug(
                "Table cell updated",
                extra={
                    "row": table.cursor_row,
                    "column": column_index,
                    "new_value": value,
                    "old_value": old_value,
                    "context": "POReviewScreen.edit_translation",
                },
            )

    def filter_callback(self, result: Any):
        """Filter the table rows based on a pattern.

        Args:
            pattern (str): The pattern to filter rows by. Supports wildcards (* and ?) and character sequences [...] or [^...].
        """
        if not isinstance(result, str):
            self.logger.warning(
                "Filter callback received non-string result, ignoring.",
                extra={"result": str(result), "context": "POReviewScreen.filter_callback"},
            )
            return

        self.logger.debug("Filtering table", extra={"pattern": result, "context": "POReviewScreen.filter"})

        tmp_table = DataTable[str](zebra_stripes=True)
        tmp_table.add_columns("", _("Type"), _("MsgId"), _("MsgStr"), _("Tag"))
        for cell in self.generate_cells():
            tmp_table.add_row(cell.row_no, cell.type, cell.msgid, cell.msgstr, cell.tag)

        table: DataTable[str] = self.query_one(DataTable)  # pyright: ignore[reportUnknownVariableType]
        selected_col = table.cursor_column
        column_name = list(tmp_table.columns.values())[selected_col].label

        table.clear()
        for cell in self.generate_cells():
            with NotifyException(self, self.logger):
                if not fnmatch(cell[selected_col], result):
                    continue

                table.add_row(cell.row_no, cell.type, cell.msgid, cell.msgstr, cell.tag)

        self.notify(
            _('Table column "{column}" filtered with "{pattern}".').format(column=column_name, pattern=result),
            timeout=2,
            title=_("✅ Success"),
        )
        self.logger.info(
            "Table filtered",
            extra={
                "pattern": result,
                "remaining_rows": len(table.rows),
                "context": "POReviewScreen.filter",
                "column": column_name,
            },
        )

    async def action_filter(self):
        """Open the filter modal."""
        self.logger.debug("Opening filter modal", extra={"context": "POReviewScreen.action_filter"})
        await self.app.push_screen(  # pyright: ignore[reportUnknownMemberType]
            POEditScreen(None, None), callback=self.filter_callback
        )
        self.logger.info("Filter modal opened", extra={"context": "POReviewScreen.action_filter"})

    async def action_edit(self):
        """Edit the currently selected entry."""
        self.logger.debug("Opening edit modal", extra={"context": "POReviewScreen.action_edit"})
        table = await wait_for_element(self.query_one, selector=DataTable)
        if table.cursor_row == len(table.rows):
            self.logger.warning(
                "No row selected for editing, aborting.",
                extra={"row": table.cursor_row, "column": table.cursor_column, "context": "POReviewScreen.action_edit"},
            )
            self.notify(
                _("Reset the filter to select an entry to edit."),
                timeout=2,
                title=_("❌ Error"),
            )
            return

        current_row = table.get_row_at(table.cursor_row)
        for entry, idx in self.entries:
            if idx is None and current_row[1] == "Singular" and escape_control_chars(entry.msgid) == current_row[2]:
                break
            elif (
                idx is not None
                and f"{current_row[1]}".startswith("Plural")
                and escape_control_chars(entry.msgid if idx == 0 else entry.msgid_plural) == current_row[2]
            ):
                break

        else:
            self.logger.error(
                "Could not find the selected entry in the entries list, aborting edit.",
                extra={
                    "row": table.cursor_row,
                    "rows": len(table.rows),
                    "column": table.cursor_column,
                    "columns": len(table.columns),
                    "context": "POReviewScreen.action_edit",
                },
            )
            self.notify(
                _("No entry found for the selected cell. Restart the application."),
                timeout=2,
                title=_("❌ Error"),
            )
            return

        await self.app.push_screen(  # pyright: ignore[reportUnknownMemberType]
            POEditScreen(entry, idx), callback=self.edit_translation_callback
        )
        self.logger.info("Edit modal opened", extra={"context": "POReviewScreen.action_edit"})

    async def action_save(self):
        """Save the PO file."""
        self.logger.info("Saving PO file...", extra={"context": "POReviewScreen.action_save"})
        self.pofile.save(str(self.pofile_path))  # pyright: ignore[reportUnknownMemberType]
        self.notify(
            _('PO file saved to "{path}".').format(path=str(self.pofile_path)),
            timeout=2,
            title=_("✅ Success"),
        )
        self.logger.info(
            "PO file saved", extra={"path": str(self.pofile_path), "context": "POReviewScreen.action_save"}
        )

    async def action_abort(self):
        """Quit without saving."""

        def callback(result: Any):
            if result:
                self.logger.info(
                    "User confirmed abort without saving", extra={"context": "POReviewScreen.action_abort.on_dismissed"}
                )
                self.dismiss()
                self.logger.info("POReviewScreen modal dismissed", extra={"context": "POReviewScreen.action_abort"})
                self.notify(
                    _("Aborted without saving any changes."),
                    timeout=2,
                    title=_("⚠️  Aborted"),
                )
            else:
                self.logger.info(
                    "User canceled abort without saving", extra={"context": "POReviewScreen.action_abort.on_dismissed"}
                )

        await self.app.push_screen(ConfirmInevitable(), callback=callback)  # pyright: ignore[reportUnknownMemberType]

    async def action_quit(self):
        """Quit and save."""
        self.logger.info("Quitting and saving...", extra={"context": "POReviewScreen.action_quit"})
        await self.action_save()
        self.dismiss()
        self.logger.info("POReviewScreen modal dismissed", extra={"context": "POReviewScreen.action_quit"})
