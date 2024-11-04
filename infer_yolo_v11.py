from ikomia import dataprocess


# --------------------
# - Interface class to integrate the process with Ikomia application
# - Inherits PyDataProcess.CPluginProcessInterface from Ikomia API
# --------------------
class IkomiaPlugin(dataprocess.CPluginProcessInterface):

    def __init__(self):
        dataprocess.CPluginProcessInterface.__init__(self)

    def get_process_factory(self):
        # Instantiate algorithm object
        from infer_yolo_v11.infer_yolo_v11_process import InferYoloV11Factory
        return InferYoloV11Factory()

    def get_widget_factory(self):
        # Instantiate associated widget object
        from infer_yolo_v11.infer_yolo_v11_widget import InferYoloV11WidgetFactory
        return InferYoloV11WidgetFactory()
