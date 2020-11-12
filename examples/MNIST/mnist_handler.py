import json
import logging
import os
import torch

logger = logging.getLogger(__name__)


class MNISTDigitClassifier(object):
    """
    MNISTDigitClassifier handler class. This handler takes a greyscale image
    and returns the digit in that image.
    """

    def __init__(self):
        self.model = None
        self.mapping = None
        self.device = None
        self.initialized = False

    def initialize(self, ctx):
        """
        First try to load torchscript else load eager mode state_dict based model

        :param ctx: System properties
        """
        properties = ctx.system_properties
        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id")) if torch.cuda.is_available() else "cpu"
        )
        model_dir = properties.get("model_dir")

        # Read model serialize/pt file
        model_pt_path = os.path.join(model_dir, "model.pth")
        self.model = torch.load(model_pt_path, map_location=self.device)
        self.model.to(self.device)
        self.model.eval()

        logger.debug("Model file %s loaded successfully", model_pt_path)
        self.initialized = True

    def preprocess(self, data):
        """
        Scales, crops, and normalizes a PIL image for a MNIST model,
         returns an Numpy array

        :param data: Input to be passed through the layers for prediction

        :return: output - Preprocessed image
        """

        image = data[0].get("data")
        if image is None:
            image = data[0].get("body")

        image = image.decode("utf-8")
        image = torch.Tensor(json.loads(image)["data"])
        return image

    def inference(self, input_data):
        """
        Predict the class (or classes) of an image using a trained deep learning model

        :param img: Input to be passed through the layers for prediction

        :return: output - Predicted label for the given input
        """

        self.model.eval()
        inputs = input_data.to(self.device)
        outputs = self.model(inputs)

        _, y_hat = outputs.max(1)
        predicted_idx = str(y_hat.item())
        return [predicted_idx]

    def postprocess(self, inference_output):
        """
        Does postprocess after inference to be returned to user

        :param inference_output: Output of inference

        :return: output - Output after post processing
        """
        return inference_output


_service = MNISTDigitClassifier()


def handle(data, context):
    """
    Default function that is called when predict is invoked

    :param data: Input to be passed through the layers for prediction
    :param context: dict containing system properties

    :return: output - Output after postprocess
    """
    if not _service.initialized:
        _service.initialize(context)

    if data is None:
        return None

    data = _service.preprocess(data)
    data = _service.inference(data)
    data = _service.postprocess(data)

    return data
