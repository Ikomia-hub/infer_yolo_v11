import copy
from ikomia import core, dataprocess, utils
from ultralytics import YOLO
import torch
import os
from ultralytics import download


# --------------------
# - Class to handle the algorithm parameters
# - Inherits PyCore.CWorkflowTaskParam from Ikomia API
# --------------------
class InferYoloV11Param(core.CWorkflowTaskParam):

    def __init__(self):
        core.CWorkflowTaskParam.__init__(self)
        self.model_name = "yolo11m"
        self.cuda = torch.cuda.is_available()
        self.input_size = 640
        self.conf_thres = 0.25
        self.iou_thres = 0.7
        self.update = False
        self.model_weight_file = ""

    def set_values(self, param_map):
        # Set parameters values from Ikomia application
        self.model_name = str(param_map["model_name"])
        self.cuda = utils.strtobool(param_map["cuda"])
        self.input_size = int(param_map["input_size"])
        self.conf_thres = float(param_map["conf_thres"])
        self.iou_thres = float(param_map["iou_thres"])
        self.model_weight_file = str(param_map["model_weight_file"])
        self.update = True

    def get_values(self):
        # Send parameters values to Ikomia application
        # Create the specific dict structure (string container)
        param_map = {}
        param_map["model_name"] = str(self.model_name)
        param_map["cuda"] = str(self.cuda)
        param_map["input_size"] = str(self.input_size)
        param_map["conf_thres"] = str(self.conf_thres)
        param_map["iou_thres"] = str(self.iou_thres)
        param_map["update"] = str(self.update)
        param_map["model_weight_file"] = str(self.model_weight_file)
        return param_map

# --------------------
# - Class which implements the algorithm
# - Inherits PyCore.CWorkflowTask or derived from Ikomia API
# --------------------
class InferYoloV11(dataprocess.CObjectDetectionTask):

    def __init__(self, name, param):
        dataprocess.CObjectDetectionTask.__init__(self, name)
        # Add input/output of the algorithm here
        # Example :  self.add_input(dataprocess.CImageIO())
        #           self.add_output(dataprocess.CImageIO())

        # Create parameters object
        if param is None:
            self.set_param_object(InferYoloV11Param())
        else:
            self.set_param_object(copy.deepcopy(param))

        self.repo = 'ultralytics/assets'
        self.version = 'v8.3.0'
        self.device = torch.device("cpu")
        self.classes = None
        self.model = None
        self.half = False
        self.model_name = None

    def get_progress_steps(self):
        # Function returning the number of progress steps for this algorithm
        # This is handled by the main progress bar of Ikomia Studio
        return 1

    def run(self):
        # Core function of your process
        # Call begin_task_run() for initialization
        self.begin_task_run()

        # Get parameters :
        param = self.get_param_object()

        # Get input :
        input = self.get_input(0)

        # Get image from input/output (numpy array):
        src_image = input.get_image()

        # Load model
        if param.update or self.model is None:
            self.device = torch.device(
                "cuda") if param.cuda and torch.cuda.is_available() else torch.device("cpu")
            self.half = True if param.cuda and torch.cuda.is_available() else False

            if param.model_weight_file:
                self.model = YOLO(param.model_weight_file)
            else:
                # Set path
                model_folder = os.path.join(os.path.dirname(
                    os.path.realpath(__file__)), "weights")
                model_weights = os.path.join(
                    str(model_folder), f'{param.model_name}.pt')
                # Download model if not exist
                if not os.path.isfile(model_weights):
                    url = f'https://github.com/{self.repo}/releases/download/{self.version}/{param.model_name}.pt'
                    download(url=url, dir=model_folder, unzip=True)
                self.model = YOLO(model_weights)
            param.update = False

        # Run detection
        results = self.model.predict(
            src_image,
            save=False,
            imgsz=param.input_size,
            conf=param.conf_thres,
            iou=param.iou_thres,
            half=self.half,
            device=self.device
        )

        # Set classe names
        self.classes = list(results[0].names.values())
        self.set_names(self.classes)

        # Get output
        boxes = results[0].boxes.xyxy
        confidences = results[0].boxes.conf
        class_idx = results[0].boxes.cls

        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, class_idx)):
            box = box.detach().cpu().numpy()
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
            widht = x2 - x1
            height = y2 - y1
            self.add_object(
                i,
                int(cls),
                float(conf),
                float(x1),
                float(y1),
                float(widht),
                float(height)
            )

        # Step progress bar (Ikomia Studio):
        self.emit_step_progress()

        # Call end_task_run() to finalize process
        self.end_task_run()


# --------------------
# - Factory class to build process object
# - Inherits PyDataProcess.CTaskFactory from Ikomia API
# --------------------
class InferYoloV11Factory(dataprocess.CTaskFactory):

    def __init__(self):
        dataprocess.CTaskFactory.__init__(self)
        # Set algorithm information/metadata here
        self.info.name = "infer_yolo_v11"
        self.info.short_description = "Inference with YOLOv11 models"
        # relative path -> as displayed in Ikomia application process tree
        self.info.path = "Plugins/Python/Detection"
        self.info.version = "1.0.0"
        self.info.icon_path = "images/icon.png"
        self.info.authors = "Jocher, G., Chaurasia, A., & Qiu, J"
        self.info.article = "YOLO by Ultralytics"
        self.info.journal = ""
        self.info.year = 2024
        self.info.license = "AGPL-3.0"
        # URL of documentation
        self.info.documentation_link = "https://docs.ultralytics.com/"
        # Code source repository
        self.info.repository = "https://github.com/Ikomia-hub/infer_yolo_v11"
        self.info.original_repository = "https://github.com/ultralytics/ultralytics"
        # Keywords used for search
        self.info.keywords = "YOLO, object, detection, ultralytics, real-time"
        self.info.algo_type = core.AlgoType.INFER
        self.info.algo_tasks = "OBJECT_DETECTION"

    def create(self, param=None):
        # Create algorithm object
        return InferYoloV11(self.info.name, param)
