"""Column name constants for Document Register Excel sheets."""

from __future__ import annotations


class Cols:
    """Column names used across the Document Register Excel sheets.

    Single source of truth — change here if the Excel layout changes.

    Sheets:
        - ``FE EDDR`` (Front-End Engineering Document Deliverable Register)
        - ``DE EDDR`` (Detailed Engineering Document Deliverable Register)
        - ``Process`` / ``Client`` / ``Mechanical`` (SharePoint file listings,
          same column layout as the legacy ``query`` sheet)
    """

    # FE EDDR sheet columns
    FE_EDDR_DOC_NO = "Document No"
    FE_EDDR_TITLE = "Title"

    # DE EDDR sheet columns
    DE_EDDR_COMPANY_DOC_NO = "COMPANY DOCUMENT NUMBER"
    DE_EDDR_DESCRIPTION = "DESCRIPTION"
    DE_EDDR_CONTRACTOR_DOC_NO = "CONTRACTOR DOCUMENT NUMBER"

    # SharePoint-extracted sheets (Process / Client / Mechanical) columns
    SP_NAME = "Name"
    SP_MODIFIED = "Modified"
    SP_MODIFIED_BY = "Modified By"
    SP_PATH = "Path"
    SP_ITEM_TYPE = "Item Type"
