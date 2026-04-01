import torch
import numpy as np
from PIL import Image
import io
import boto3
import time
import os

class BackblazeUploader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "endpoint_url": ("STRING", {"default": "https://s3.eu-central-003.backblazeb2.com"}),
                "key_id": ("STRING", {"default": ""}),
                "application_key": ("STRING", {"default": ""}),
                "bucket_name": ("STRING", {"default": ""}),
                "file_name_prefix": ("STRING", {"default": "comfy_gen"}),
                "extension": (["png", "jpg", "webp"], {"default": "png"}),
                "naming_mode": (["strict", "timestamp", "sequential"], {"default": "sequential"}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("url_list",)
    FUNCTION = "upload_images"
    OUTPUT_NODE = True
    CATEGORY = "Cloud Storage"

    def upload_images(self, images, endpoint_url, key_id, application_key, bucket_name, file_name_prefix, extension, naming_mode):
        if not endpoint_url.startswith('http'):
            endpoint_url = f'https://{endpoint_url}'

        s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key
        )
        
        uploaded_urls = []
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        # Логика определения начального индекса для режима sequential
        next_idx = 1
        if naming_mode == "sequential":
            try:
                response = s3.list_objects_v2(Bucket=bucket_name, Prefix=file_name_prefix)
                next_idx = response.get('KeyCount', 0) + 1
            except Exception as e:
                print(f"!!! Backblaze List Error: {str(e)}")
                # Если не удалось получить список, начнем с 1 или выдадим ошибку

        for i, image in enumerate(images):
            # Подготовка изображения
            i_image = 255. * image.cpu().numpy()
            img = Image.fromarray(np.uint8(i_image))
            buffer = io.BytesIO()
            img.save(buffer, format=extension.upper())
            buffer.seek(0)
            
            # Сборка имени файла в зависимости от режима
            name_parts = [file_name_prefix]
            
            if naming_mode == "timestamp":
                name_parts.append(timestamp)
                # Если в батче несколько фото, добавляем индекс внутри батча
                if len(images) > 1:
                    name_parts.append(str(i))
                    
            elif naming_mode == "sequential":
                current_file_idx = next_idx + i
                name_parts.append(f"{current_file_idx:04d}")
            
            # В режиме 'strict' используется только file_name_prefix (и индекс i, если фото > 1)
            elif naming_mode == "strict" and len(images) > 1:
                name_parts.append(str(i))

            full_filename = f"{'_'.join(name_parts)}.{extension}"
            
            try:
                s3.upload_fileobj(
                    buffer, 
                    bucket_name, 
                    full_filename,
                    ExtraArgs={'ContentType': f'image/{extension}'}
                )
                base_url = endpoint_url.rstrip('/')
                url = f"{base_url}/{bucket_name}/{full_filename}"
                uploaded_urls.append(url)
                
            except Exception as e:
                print(f"!!! Backblaze Upload Error: {str(e)}")
                return (f"Error: {str(e)}",)

        return (", ".join(uploaded_urls),)

NODE_CLASS_MAPPINGS = {"BackblazeUploader": BackblazeUploader}
NODE_DISPLAY_NAME_MAPPINGS = {"BackblazeUploader": "☁️ Backblaze B2 Uploader"}