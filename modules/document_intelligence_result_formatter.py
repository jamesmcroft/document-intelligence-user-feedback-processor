import datetime
import json
from typing import Dict
from azure.ai.formrecognizer import (AnalyzeResult)
from azure.core.serialization import AzureJSONEncoder
from modules.document_intelligence_label import DocumentIntelligenceLabel


class DocumentIntelligenceResultFormatter:
    @staticmethod
    def save_to_labels_json(result: list[DocumentIntelligenceLabel], pdf_file_name: str, json_file_path: str):
        """Save the results of document labeling to a JSON file in the expected format for Azure AI Document Intelligence.

        :param results: The results of the document labeling.
        :param json_file_path: The path to the JSON file where the result will be saved.
        :return: The reformatted result of the Document Intelligence labels as a dictionary.
        """

        ordered_labels = sorted(result, key=lambda x: x.label)
    
        labels_result = {
            "$schema": "https://schema.cognitiveservices.azure.com/formrecognizer/2021-03-01/labels.json",
            "document": pdf_file_name,
            "labels": [label.as_label() for label in ordered_labels]
        }

        r = json.dumps(labels_result)

        with open(json_file_path, 'w') as json_file:
            json.dump(json.loads(r), json_file, indent=4, cls=AzureJSONEncoder)

        return labels_result

    @staticmethod
    def save_to_ocr_json(result: AnalyzeResult, json_file_path: str):
        """Save the result of a Document Intelligence analysis to a JSON file.

        :param result: The result of the Document Intelligence analysis.
        :param json_file_path: The path to the JSON file where the result will be saved.
        :return: The reformatted result of the Document Intelligence analysis as a dictionary.
        """

        date = datetime.datetime.now(
            datetime.UTC).__format__('%Y-%m-%dT%H:%M:%SZ')

        analyzeResult = result.to_dict()

        ocr_result = {
            "status": "succeeded",
            "createdDateTime": date,
            "lastUpdatedDateTime": date,
            "analyzeResult": DocumentIntelligenceResultFormatter.reformat_analyze_result_dict(analyzeResult),
        }

        r = json.dumps(ocr_result)

        with open(json_file_path, 'w') as json_file:
            json.dump(json.loads(r), json_file, indent=4, cls=AzureJSONEncoder)

        return ocr_result

    @staticmethod
    def reformat_analyze_result_dict(analyze_result_dict: Dict):
        """Reformats the AnalyzeResult dictionary output into the expected format for Azure AI Document Intelligence.

        Converts the keys of the dictionary, recursively through all nested dictionaries or array of dictionaries, to camel case (e.g., from my_property to myProperty).
        Updates any "polygon" key values from [{'x': 0, 'y': 0}] to [x, y, x, y, ...].

        :param dictionary: The dictionary to convert.
        :return: The dictionary with the keys converted to camel case.
        """

        result = {}
        for key, value in analyze_result_dict.items():
            if isinstance(value, dict):
                value = DocumentIntelligenceResultFormatter.reformat_analyze_result_dict(
                    value)
            elif isinstance(value, list):
                value = [DocumentIntelligenceResultFormatter.reformat_analyze_result_dict(
                    item) for item in value]

            if key == "polygon":
                value = [coord for point in value for coord in point.values()]

            result[DocumentIntelligenceResultFormatter.__to_camel_case__(
                key)] = value

        return result

    @staticmethod
    def __to_camel_case__(snake_str: str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
