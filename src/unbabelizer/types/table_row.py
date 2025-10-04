from typing import TYPE_CHECKING, NamedTuple, Tuple, overload

from textual.widgets import DataTable

if TYPE_CHECKING:

    @overload
    def _(message: str) -> str: ...  # pyright: ignore[reportInconsistentOverload, reportNoOverloadImplementation]


class TableRow(NamedTuple):
    """A cell in the PO review table."""

    row_no: int
    type: str
    msgid: str
    msgstr: str
    tag: str
    note: str

    @property
    def actual_row(self) -> Tuple[str, ...]:
        """Return the actual row data without the row number."""
        return self[1:]

    @classmethod
    def define_columns(cls, table: DataTable[str]):
        """Add columns to the given DataTable for displaying TableCell data.

        Args:
            table (DataTable[str]): The DataTable to add columns to.
        """
        table.add_column(_("Type"), key="type")
        table.add_column(_("MsgId"), key="msgid")
        table.add_column(_("MsgStr"), key="msgstr")
        table.add_column(_("Tag"), key="tag")
        table.add_column(_("Note"), key="note")

    def add_to_table(self, table: DataTable[str]):
        """Add this TableRow to the given DataTable.

        Args:
            table (DataTable[str]): The DataTable to add the row to.
        """
        table.add_row(
            *self.actual_row,
            key=f"{self.row_no:d}",
            label=f"{self.row_no:d}",
        )
