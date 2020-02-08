"""API which controls Google Spreadsheet."""
import logging
import auth
from sheet import Sheet


logging.basicConfig(
    filename="logs.txt",
    format="[%(levelname)s] %(asctime)s: %(message)s",
    level=logging.INFO,
)


class Spreadsheet:
    """Object related to a Google spreadsheet.

    Uses `config` attr to update spreasheet structure.
    Requires manual configurations reloading.

    Args:
        config (module):
            Imported config.py module with all of the
            spreadsheet preferences.

        id_ (str):
            Id of the related spreadsheet. If not given,
            new spreadsheet will be created.
    """

    def __init__(self, config, id_=None):
        self._config = config
        self._ss_resource = auth.authenticate()
        self._id = id_ or self._create()
        self.sheets = self._init_sheets()

    @property
    def id(self):
        """Spreadsheet id."""
        return self._id

    @id.setter
    def id(self, value):
        """Spreadsheet id setter."""
        raise AttributeError(
            "Spreadsheet id can't be changed. Initiate another Spreadsheet() object."
        )

    def update_structure(self):
        """Update spreadsheet structure.

        Rename the spreadsheet, if name in `config` has been
        changed. Add new sheets into the spreadsheet, delete
        sheets deleted from the configurations.
        """
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
                sheet.update(self._ss_resource)
                logging.info("Updated sheet " + sheet_name)
            except Exception:
                logging.exception("Exception occured:")

    def reload_config(self, config):
        """Save new config.py module.

        Args:
            config (module):
                Imported config.py module with all preferences.
        """
        self._config = config
        for sheet_name, sheet in self.sheets.items():
            sheet.reload_config(self._config.SHEETS[sheet_name])

    def _init_sheets(self):
        """Init Sheet object for every sheet in this spreadsheet.

        Returns:
            dict: {<sheet_name>: <sheet.Sheet>} - sheets index.
        """
        sheets = {}
        resp = self._ss_resource.get(spreadsheetId=self._id).execute()

        for sheet in resp["sheets"]:
            props = sheet["properties"]
            sheets[props["title"]] = Sheet(props["title"], self._id, props["sheetId"])

        return sheets

    def _actualize_sheets(self):
        """Update sheets index of this spreadsheet.

        This method removes Sheet object of the sheets which were
        deleted, sets ids for Sheet objects of newly created sheets.
        """
        sheets_in_spreadsheet = []
        to_delete = []

        resp = self._ss_resource.get(spreadsheetId=self._id).execute()
        for sheet in resp["sheets"]:
            props = sheet["properties"]
            self.sheets[props["title"]].id = props["sheetId"]
            sheets_in_spreadsheet.append(props["title"])

        for sheet_name, sheet in self.sheets.items():
            if sheet_name not in sheets_in_spreadsheet:
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
        new_sheets_reqs = []

        for sheet_name in sheets_in_conf:
            if sheet_name not in self.sheets.keys():
                self.sheets[sheet_name] = Sheet(sheet_name, self._id)
                new_sheets_reqs.append(self.sheets[sheet_name].create_request)

        return new_sheets_reqs

    def _build_delete_sheets_requests(self, sheets_in_conf):
        """
        Build delete requests for the sheets, which
        haven't been found in the configurations.

        Args:
            sheets_in_conf (tuple): Sheets list from the configurations.

        Returns:
            list: List of delete-sheet requests.
        """
        del_sheets_reqs = []

        for sheet_name, sheet in self.sheets.items():
            if sheet_name not in sheets_in_conf:
                del_sheets_reqs.append(sheet.delete_request)

        return del_sheets_reqs

    def _create(self):
        """Create new spreadsheet according to config.

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
    """Build dicts with the sheet preferences.

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
