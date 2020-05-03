"""API to control Google Spreadsheet."""
import importlib
import logging
import os.path
import auth
from sheet import Sheet, ArchiveSheet


logging.basicConfig(
    filename="logs.txt",
    format="[%(levelname)s] %(asctime)s: %(message)s",
    level=logging.INFO,
)


class Spreadsheet:
    """Object related to a concrete Google spreadsheet.

    Uses `config` attr to designate spreadsheet structure.
    Requires manual configurations reloading.

    Args:
        config (module):
            Imported config.py module with all of the
            spreadsheet preferences.
        id_ (str):
            Id of the related spreadsheet. If not given,
            new spreadsheet will be created on object init.
    """

    def __init__(self, config, id_=None):
        self._last_config_update = 0
        self._config_updated = False
        self._config = config
        self._archive = None
        self._to_be_archived = {}

        self._ss_resource = auth.authenticate()
        self._id = id_ or self._create()
        self.sheets = self._init_existing_sheets()
        if self._config.ARCHIVE_SHEET and not self._archive:
            self._archive = ArchiveSheet(
                config.ARCHIVE_SHEET["name"], self.id, is_new=True
            )

    @property
    def id(self):
        """Spreadsheet id."""
        return self._id

    @id.setter
    def id(self, value):
        """Spreadsheet id setter.

        Args:
            value (Any): New attribute value.
        """
        raise AttributeError(
            "Spreadsheet id can't be changed. Initiate another Spreadsheet() object."
        )

    def update_structure(self, force=False):
        """Update spreadsheet structure.

        If configurations were changed, rename the spreadsheet,
        add new sheets into the spreadsheet and delete
        sheets deleted from the configurations.

        Args:
            force (bool):
                If True, structure will be updated whether
                configuration were updated or not.
        """
        if not (self._config_updated or force):
            return
        try:
            logging.info("Updating spreadsheet {id_} structure".format(id_=self._id))
            # spreadsheet rename request
            requests = [
                {
                    "updateSpreadsheetProperties": {
                        "properties": {"title": self._config.TITLE},
                        "fields": "title",
                    }
                }
            ]
            sheets_in_conf = tuple(self._config.SHEETS.keys())

            requests += self._build_new_sheets_requests(sheets_in_conf)
            requests += self._build_delete_sheets_requests(sheets_in_conf)

            self._ss_resource.batchUpdate(
                spreadsheetId=self._id, body={"requests": requests}
            ).execute()

            if len(requests) > 1:  # not only rename request
                self._actualize_sheets()

            logging.info("Updated spreadsheet {id_} structure".format(id_=self._id))
        except Exception:
            logging.exception("Exception occured:")

    def update_all_sheets(self):
        """Update all the sheets one by one."""
        for sheet_name, sheet in self.sheets.items():
            logging.info("Updating sheet " + sheet_name)
            try:
                sheet.update(self._ss_resource, self._to_be_archived)
                logging.info("Updated sheet " + sheet_name)
            except Exception:
                logging.exception("Exception occured:")

        if self._archive:
            logging.info("Updating archive")
            try:
                self._archive.update(self._ss_resource, self._to_be_archived)
                self._to_be_archived = {}
            except Exception:
                logging.exception("Exception occured:")
            logging.info("Archive updated")

    def reload_config(self, config):
        """Load new configurations.

        Reload configurations and set them to this
        spreadsheet and all of its sheets.

        Args:
            config (module):
                Imported config.py module with preferences.
        """
        # reload configurations and filling functions modules
        config.fill_funcs = importlib.reload(config.fill_funcs)
        config = importlib.reload(config)

        config_update = os.path.getmtime(config.__file__)
        self._config_updated = config_update != self._last_config_update

        if self._config_updated:
            self._config = config
            for sheet_name, sheet in self.sheets.items():
                if sheet_name in self._config.SHEETS:
                    sheet.reload_config(self._config.SHEETS[sheet_name])

            if self._archive:
                self._archive.reload_config(self._config.ARCHIVE_SHEET)

            self._last_config_update = config_update

    def _init_existing_sheets(self):
        """Init Sheet() object for every sheet in this spreadsheet.

        Returns:
            dict: {<sheet_name>: <sheet.Sheet>} - sheets index.
        """
        sheets = {}
        resp = self._ss_resource.get(spreadsheetId=self._id).execute()

        for sheet in resp["sheets"]:
            props = sheet["properties"]
            name = props["title"]

            if name == self._config.ARCHIVE_SHEET.get("name"):
                self._archive = ArchiveSheet(name, self._id, props["sheetId"])
                continue

            sheets[name] = Sheet(name, self._id, props["sheetId"])

        return sheets

    def _actualize_sheets(self):
        """Update sheets index of this spreadsheet.

        Removes Sheet() objects of the sheets which were not
        found in configurations, and sets ids for the Sheet()
        objects of newly created sheets.
        """
        sheets_in_ss = []

        resp = self._ss_resource.get(spreadsheetId=self._id).execute()
        # update sheets ids from the real spreadsheet
        for sheet in resp["sheets"]:
            props = sheet["properties"]
            name = props["title"]

            if name == self._config.ARCHIVE_SHEET.get("name"):
                self._archive.id = props["sheetId"]
                continue

            self.sheets[name].id = props["sheetId"]
            sheets_in_ss.append(name)

        to_delete = []
        # check for Sheet()'s, which are no more in the spreadsheet
        for sheet_name, sheet in self.sheets.items():
            if sheet_name not in sheets_in_ss:
                to_delete.append(sheet_name)
                continue

        for sheet_name in to_delete:
            self.sheets.pop(sheet_name)

    def _build_new_sheets_requests(self, sheets_in_conf):
        """Build add-new-sheet requests for the new sheets.

        Args:
            sheets_in_conf (tuple): Sheets list from the configurations.

        Returns:
            list: List of add-new-sheet requests.
        """
        add_sheet_reqs = []

        for name in sheets_in_conf:
            if name not in self.sheets.keys():
                self.sheets[name] = Sheet(name, self._id)
                add_sheet_reqs.append(self.sheets[name].create_request)

        if self._config.ARCHIVE_SHEET and self._archive.is_new:
            add_sheet_reqs.append(self._archive.create_request)
            self._archive.is_new = False

        return add_sheet_reqs

    def _build_delete_sheets_requests(self, sheets_in_conf):
        """
        Build delete requests for the sheets, which
        haven't been found in the configurations.

        Args:
            sheets_in_conf (tuple): Sheets list from the configurations.

        Returns:
            list: List of delete-sheet requests.
        """
        del_sheet_reqs = []

        for name, sheet in self.sheets.items():
            if name not in sheets_in_conf:
                del_sheet_reqs.append(sheet.delete_request)

        if self._archive and not self._config.ARCHIVE_SHEET:
            del_sheet_reqs.append(self._archive.delete_request)

        return del_sheet_reqs

    def _create(self):
        """Create new spreadsheet according to configurations.

        Returns:
            str: The new spreadsheet id.
        """
        spreadsheet = self._ss_resource.create(
            body={
                "properties": {"title": self._config.TITLE},
                "sheets": _gen_sheets_struct(self._config.SHEETS.keys()),
            }
        ).execute()
        return spreadsheet.get("spreadsheetId")


def _gen_sheets_struct(sheets_config):
    """Build dicts with the sheets preferences.

    Args:
        sheets_config (dict): Sheets preferences.

    Returns:
        List of dicts, each of which represents structure
        for passing into Google Spreadsheet API requests.
    """
    sheets = []
    for sheet_name in sheets_config:
        sheets.append({"properties": {"title": sheet_name}})

    return sheets
