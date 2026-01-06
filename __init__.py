from .backblaze_uploader import NODE_CLASS_MAPPINGS as uploader_mappings
from .backblaze_loader import NODE_CLASS_MAPPINGS as loader_mappings

NODE_CLASS_MAPPINGS = {**uploader_mappings, **loader_mappings}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BackblazeUploader": "☁️ Backblaze B2 Uploader",
    "BackblazeLoader": "☁️ Backblaze B2 Loader"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
