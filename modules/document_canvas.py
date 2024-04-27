from pdf2image import convert_from_path
import os
import json
from azure.ai.formrecognizer import (AnalyzeResult)
from jupyter_bbox_widget import BBoxWidget


class DocumentCanvas:
    """ A class to represent a document canvas that allows users to draw over a document to provide feedback with."""

    def __init__(self, working_dir: str):
        """Initializes the DocumentCanvas.

        :param working_dir: The current working directory for storing files processed by the DocumentCanvas.
        """

        self.canvases: list[BBoxWidget] = []
        self.images_dir = os.path.join(working_dir, 'images')
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

    def load_pdf(self, pdf_file_path: str, fields_file_path: str, analysis_result_path: str | None = None) -> list[BBoxWidget]:
        """Loads a PDF file, converts it to images, and creates canvases for each page of the PDF file.

        :param pdf_file_path: The path to the PDF file to load.
        :param analysis_result_path: The path to the analysis result file to load if available.
        :return: A list of canvases representing the pages of the PDF file.
        """

        pdf_file_name = os.path.basename(pdf_file_path)
        pages = convert_from_path(pdf_file_path, fmt='jpeg')

        with open(fields_file_path, 'r') as file:
            self.fields: dict = json.load(file)
            # Set the initial canvas fields, excluding any fieldType that is 'array'
            self.field_options = [
                field['fieldKey'] for field in self.fields['fields'] if field['fieldType'] != 'array']

        analysis_result = None
        if analysis_result_path is not None:
            with open(analysis_result_path, 'r') as file:
                analysis_result = json.load(file)['analyzeResult']

        for i, page in enumerate(pages):
            page_ref = i + 1
            image_path_ref = os.path.join(
                self.images_dir, f'{pdf_file_name}.page_{page_ref}.jpg')
            page.save(image_path_ref, 'JPEG')

            canvas = BBoxWidget(
                image=image_path_ref,
                classes=self.field_options)

            canvas.image_path_ref = image_path_ref
            canvas.page_ref = page_ref
            canvas.width = page.width
            canvas.height = page.height

            if analysis_result_path is not None:
                self.render_label_regions(
                    canvas, page_ref, analysis_result)

            self.canvases.append(canvas)

        return self.canvases

    def render_label_regions(self, canvas: BBoxWidget, page_number: int, analysis_result: dict):
        """Renders the label regions on the canvas for the specified page number.

        :param canvas: The canvas to render the label regions on.
        :param page_number: The page number to render the label regions on.
        :param analysis_result: The analysis result containing the label regions to render.
        """

        canvas_width = canvas.width
        canvas_height = canvas.height
        page_width = analysis_result['pages'][page_number - 1]['width']
        page_height = analysis_result['pages'][page_number - 1]['height']
        width = canvas_width / page_width
        height = canvas_height / page_height

        if len(analysis_result['documents']) == 0:
            print('No documents found in the analysis result')
            return

        document_fields: dict = analysis_result['documents'][0]['fields']
        bboxes = self._get_bboxes__(
            document_fields, page_number, width, height)

        canvas.bboxes = bboxes

    def _get_bboxes__(self, fields_result: dict, page_number: int, width: int, height: int, parent_field: str | None = None, row_number: int | None = None):
        bboxes = []

        for fieldKey in fields_result.keys():
            field_value: dict = fields_result[fieldKey]

            if (field_value['valueType'] == 'list'):
                field_value_list: list = field_value['value']
                for field_value_item in field_value_list:
                    bboxes.extend(self._get_bboxes__(
                        field_value_item['value'], page_number, width, height, fieldKey, field_value_list.index(field_value_item)))

            if len(field_value['boundingRegions']) == 0:
                continue

            bboxes.append(self.__get_bbox__(
                fieldKey, field_value, page_number, width, height, parent_field, row_number))

        return bboxes

    def __get_bbox__(self, fieldKey: str, fieldValue: dict, page_number: int, width: int, height: int, parent_field: str | None = None, row_number: int | None = None):
        field_bounding_region: dict = fieldValue['boundingRegions'][0]
        if field_bounding_region['pageNumber'] == page_number:
            field_bounding_region_polygon: list = field_bounding_region['polygon']

            field_bounding_region_x = field_bounding_region_polygon[0] * width
            field_bounding_region_y = field_bounding_region_polygon[1] * height
            field_bounding_region_width = (
                field_bounding_region_polygon[2] - field_bounding_region_polygon[0]) * width
            field_bounding_region_height = (
                field_bounding_region_polygon[5] - field_bounding_region_polygon[1]) * height

            return {
                "x": field_bounding_region_x,
                "y": field_bounding_region_y,
                "width": field_bounding_region_width,
                "height": field_bounding_region_height,
                "label": fieldKey,
                "content": fieldValue['content'],
                "field": fieldKey if parent_field is None else parent_field,
                "row_field": fieldKey,
                "row_number": row_number
            }

    def get_document_labels(self):
        """Gets the document labels from the canvases.

        :return: The document labels.
        """

        document_labels = []
        for canvas in self.canvases:
            for bbox in canvas.bboxes:
                document_label = DocumentLabel(
                    canvas.image_path_ref,
                    canvas.page_ref, 
                    bbox)
                document_label.normalize(canvas.width, canvas.height)
                document_labels.append(document_label)
        return document_labels


class DocumentLabel:
    """ A class to represent a bordered region in which a user can draw over a document to provide feedback with a label.

    A label region tracks the start and end points drawn by the user.

    It also provides the necessary logic for normalizing the region coordinates to the canvas size, and extracting text from the region using OCR.
    """

    def __init__(self, image_path_ref: str, page_ref: int, data: dict):
        """Initializes the DocumentLabel.

        :param image_path_ref: The path to the image file that the region is drawn on.
        :param page_ref: The page number that the region is drawn on.
        :param data: The data for the region.
        """

        self.image_path_ref = image_path_ref
        self.page_ref = page_ref
        self.label = data['label']
        self.content = data['content']
        self.field = data['field']
        self.row_field = data['row_field']
        self.row_number = str(data['row_number'])
        self.start_x = data['x']
        self.start_y = data['y']
        self.end_x = data['x'] + data['width']
        self.end_y = data['y'] + data['height']

    def normalize(self, render_width: int, render_height: int):
        """Normalizes the region coordinates to the canvas size.

        : param canvas: The canvas that the region is drawn on.
        """

        self.start_x_normalized = self.start_x / render_width
        self.start_y_normalized = self.start_y / render_height
        self.end_x_normalized = self.end_x / render_width
        self.end_y_normalized = self.end_y / render_height

    def get_bounding_box(self):
        """Gets the bounding box of the region.

        : return: The coordinates of the bounding box.
        """

        return [(self.start_x, self.start_y), (self.end_x, self.end_y)]

    def get_normalized_bounding_box(self):
        """Gets the normalized bounding box of the region.

        : return: The normalized coordinates of the bounding box.
        """

        return [self.start_x_normalized, self.start_y_normalized, self.end_x_normalized, self.start_y_normalized, self.end_x_normalized, self.end_y_normalized, self.start_x_normalized, self.end_y_normalized]
