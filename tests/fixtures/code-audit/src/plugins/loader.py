import importlib
import os


def load_optional_plugin(app):
    module_name = os.environ["APP_PLUGIN_MODULE"]
    plugin = importlib.import_module(module_name)
    plugin.register(app)
