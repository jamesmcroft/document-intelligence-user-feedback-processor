from modules.document_canvas import (DocumentLabel)
from ipywidgets import (Dropdown, Text, VBox, Label)


class DocumentIntelligenceLabel:
    """A class representing a label for a document intelligence model.

    This class is used to create a visual object that allows users to label regions in a document.
    """

    def __init__(self, label: DocumentLabel, fields: dict):
        """Initializes the DocumentIntelligenceLabel.

        :param border: The object representing the region to label.
        :param fields: The fields to choose from when labeling the region.
        """

        self.label = label.label
        self.field = label.field
        self.item_row_number = label.row_number
        self.item_row_field = label.row_field
        self.label_type = None
        self.text = label.content
        self.border = label
        self.fields = fields

        self.ui_field = None
        self.ui_text = None
        self.ui_bounding_box = None
        self.ui_row_number = None
        self.ui_row_field = None
        self.ui_row_container = None
        self.ui_container = None

    def render(self):
        """Renders the label UI.

        :return: The UI container for the label.
        """

        field_options = ['']
        for field in self.fields['fields']:
            field_options.append(field['fieldKey'])

        self.ui_field = Dropdown(
            options=field_options,
            description='Field:',
            continuous_update=True,
            value=self.field
        )
        self.ui_field.observe(self.__handle_field_change__, names='value')

        self.ui_text = Text(
            value=self.text,
            description='Text:',
            continuous_update=True
        )
        self.ui_text.observe(self.__handle_text_change__, names='value')

        self.ui_bounding_box = Label(value=f'Bounding Box: {
                                     self.border.get_bounding_box()}')

        self.ui_container = VBox(
            [self.ui_field, self.ui_text, self.ui_bounding_box])
        
        self.__setup_field_ui__()

        return self.ui_container

    def __handle_field_change__(self, change):
        """Handles the change for the field type dropdown.

        :param change: The change event.
        """

        self.field = change.new
        self.__setup_field_ui__()

    def __setup_field_ui__(self):
        field_option = next(
            (x for x in self.fields['fields'] if x['fieldKey'] == self.field), None)
        if field_option:
            if field_option['fieldType'] == "array":
                itemType = field_option['itemType']
                definition = self.fields['definitions'][itemType]

                # Add a text box to the existing vbox for the row number
                self.ui_row_number = Text(
                    value=self.item_row_number,
                    description='Row Number:',
                    continuous_update=True
                )
                self.ui_row_number.observe(
                    self.__handle_row_number_change__, names='value')

                row_field_options = ['']
                for row_field in definition['fields']:
                    row_field_options.append(row_field['fieldKey'])

                self.ui_row_field = Dropdown(
                    options=row_field_options,
                    description='Row Field:',
                    continuous_update=True,
                    value=self.item_row_field
                )
                self.ui_row_field.observe(
                    self.__handle_row_field_change__, names='value')

                self.ui_row_container = VBox(
                    [self.ui_row_number, self.ui_row_field])
                self.ui_container.children = self.ui_container.children + \
                    (self.ui_row_container,)
                
                self.__set_row_label__()
            else:
                self.label = self.field

                if field_option['fieldType'] == "signature":
                    self.text = ""
                    self.label_type = "region"
                else:
                    self.label_type = None

                if self.ui_row_container is not None:
                    self.ui_container.children = self.ui_container.children[:-1]
                    self.ui_row_container = None

    def __handle_text_change__(self, change):
        """Handles the change for a text box.

        :param change: The change event.
        """

        self.text = change.new

    def __handle_row_number_change__(self, change):
        """Handles the change for the row number text box of a table.

        :param change: The change event.
        """

        self.item_row_number = change.new
        self.__set_row_label__()

    def __handle_row_field_change__(self, change):
        """Handles the change for the row field dropdown of a table.

        :param change: The change event.
        """

        self.item_row_field = change.new
        self.__set_row_label__()

    def __set_row_label__(self):
        """Sets the label for a row in a table."""

        self.label = f"{
            self.field}/{self.item_row_number}/{self.item_row_field}"
        self.label_type = None

    def as_label(self):
        """Returns the label in the desired Document Intelligence format.

        :return: The JSON object representing the label.
        """

        label_json = {
            "label": self.label,
            "value": [
                {
                    "page": self.border.page_ref,
                    "text": self.text,
                    "boundingBoxes": [self.border.get_normalized_bounding_box()]
                }
            ],
        }

        if self.label_type is not None:
            label_json['labelType'] = self.label_type

        return label_json
