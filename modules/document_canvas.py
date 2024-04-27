from pdf2image import convert_from_path
from ipycanvas import Canvas
from ipywidgets import Image
import os
import pytesseract
import cv2


class DocumentCanvas:
    """ A class to represent a document canvas that allows users to draw over a document to provide feedback with."""

    def __init__(self, working_dir: str):
        """Initializes the DocumentCanvas.

        :param working_dir: The current working directory for storing files processed by the DocumentCanvas.
        """

        self.label_regions = []
        self.images_dir = os.path.join(working_dir, 'images')
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)

    def load_pdf(self, pdf_file_path: str):
        """Loads a PDF file, converts it to images, and creates canvases for each page of the PDF file.

        :param pdf_file_path: The path to the PDF file to load.
        :return: A list of canvases representing the pages of the PDF file.
        """

        pdf_file_name = os.path.basename(pdf_file_path)
        pages = convert_from_path(pdf_file_path, fmt='jpeg')

        print(f'Loaded {len(pages)} pages')

        canvases = [Canvas(width=page.width, height=page.height)
                    for page in pages]

        for i, page in enumerate(pages):
            page_ref = i + 1
            image_path_ref = os.path.join(
                self.images_dir, f'{pdf_file_name}.page_{page_ref}.jpg')
            page.save(image_path_ref, 'JPEG')

            canvases[i].image_path_ref = image_path_ref
            canvases[i].page_ref = page_ref

            canvases[i].draw_image(Image.from_file(
                image_path_ref), 0, 0, pages[i].width, pages[i].height)
            canvases[i].on_mouse_down(
                lambda x, y: self.__handle_mouse_down_start_draw__(canvases[i], x, y))
            canvases[i].on_mouse_up(
                lambda x, y: self.__handle_mouse_down_end_draw__(canvases[i], x, y))

        return canvases

    def __handle_mouse_down_start_draw__(self, canvas: Canvas, x, y):
        """Handles the start of drawing a label region on the canvas.

        :param canvas: The canvas to draw the label region on.
        :param x: The x-coordinate of the start point.
        :param y: The y-coordinate of the start point.
        """

        label_region = LabelRegion(canvas.image_path_ref, canvas.page_ref)
        label_region.start(x, y)
        self.label_regions.append(label_region)

    def __handle_mouse_down_end_draw__(self, canvas: Canvas, x, y):
        """Handles the end of drawing a label region on the canvas.

        :param canvas: The canvas to draw the label region on.
        :param x: The x-coordinate of the end point.
        :param y: The y-coordinate of the end point.
        """

        square_border = self.label_regions[-1]
        square_border.end(x, y)
        square_border.draw(canvas)


class LabelRegion:
    """ A class to represent a bordered region in which a user can draw over a document to provide feedback with a label.

    A label region tracks the start and end points drawn by the user.

    It also provides the necessary logic for normalizing the region coordinates to the canvas size, and extracting text from the region using OCR.
    """

    def __init__(self, image_path_ref: str, page_ref: int, border_width=2, border_color='black'):
        """Initializes the LabelRegion.

        : param image_path_ref: The path to the image file that the region is drawn on.
        : param page_ref: The page number of the document that the region is drawn on.
        : param border_width: The width of the border of the region.
        : param border_color: The color of the border of the region.
        """

        self.image_path_ref = image_path_ref
        self.page_ref = page_ref
        self.border_width = border_width
        self.border_color = border_color
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None

    def start(self, x, y):
        """Sets the start point of the region.

        : param x: The x-coordinate of the start point.
        : param y: The y-coordinate of the start point.
        """

        self.start_x = x
        self.start_y = y

    def end(self, x, y):
        """Sets the end point of the region.

        : param x: The x-coordinate of the end point.
        : param y: The y-coordinate of the end point.
        """

        self.end_x = x
        self.end_y = y

    def draw(self, canvas: Canvas):
        """Draws the region on the canvas.

        : param canvas: The canvas to draw the region on.
        """

        canvas.stroke_style = self.border_color
        canvas.line_width = self.border_width
        canvas.stroke_rect(self.start_x, self.start_y,
                           self.end_x - self.start_x, self.end_y - self.start_y)
        self.normalize(canvas)

    def normalize(self, canvas: Canvas):
        """Normalizes the region coordinates to the canvas size.

        : param canvas: The canvas that the region is drawn on.
        """

        self.start_x_normalized = self.start_x / canvas.width
        self.start_y_normalized = self.start_y / canvas.height
        self.end_x_normalized = self.end_x / canvas.width
        self.end_y_normalized = self.end_y / canvas.height

    def extract_text(self):
        """Extracts text from the region using OCR.

        : return: The extracted text.
        """

        try:
            start_x_int = int(self.start_x)
            start_y_int = int(self.start_y)
            end_x_int = int(self.end_x)
            end_y_int = int(self.end_y)

            img = cv2.imread(self.image_path_ref)
            crop_img = img[start_y_int:end_y_int, start_x_int:end_x_int]
            return pytesseract.image_to_string(crop_img)
        except:
            return ''

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
