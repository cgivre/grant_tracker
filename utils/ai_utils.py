import ast
import base64
import os
import pathlib
from functools import lru_cache
from mimetypes import guess_type
from dotenv import load_dotenv

from openai import OpenAI

from utils.constants import INVOICE_PROMPT, INVOICE_USER_PROMPT
from streamlit.logger import get_logger

st_logger = get_logger(__name__)
load_dotenv()


class AIUtils:
    OPENAI_KEY = os.environ["OPENAI_KEY"]

    def __init__(self):
        self.__client = OpenAI(api_key=AIUtils.OPENAI_KEY)
        self.__model = "gpt-4o"

    def get_client(self) -> OpenAI:
        return self.__client

    # @lru_cache()
    def analyze_image(self, image_path: pathlib.Path) -> dict:
        """
        Analyzes an image of an invoice.
        :param image_path: The invoice file.
        :return: A json object containing information about the invoice.
        """
        data_url = AIUtils.local_image_to_data_url(str(image_path.absolute()))

        response = self.__client.chat.completions.create(
            model=self.__model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": INVOICE_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": INVOICE_USER_PROMPT,
                        },
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            max_tokens=4000,
        )
        # content = response.choices[0].message.json()
        raw_json = response.choices[0].message.model_dump_json(include='content')

        result = ast.literal_eval(raw_json)
        print(f"JSON1 JSON1: {result}")
        final_result = ast.literal_eval(result['content'])
        print(f"JSON JSON: {final_result}")
        return {"image_file": image_path, "invoice_information": final_result}

    @staticmethod
    def local_image_to_data_url(image_path: str) -> str:
        """
        Converts in image into Base64 format.
        :param image_path: The input image file
        :return: A string of the image in base64 format
        """
        # Guess the MIME type of the image based on the file extension
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = "application/octet-stream"  # Default MIME type if none is found

        # Read and encode the image file
        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode("utf-8")

        # Construct the data URL
        return f"data:{mime_type};base64,{base64_encoded_data}"
