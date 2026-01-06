import torch
import numpy as np
from PIL import Image, ImageOps
import io
import boto3

class BackblazeLoader:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "endpoint_url": ("STRING", {"default": "https://s3.eu-central-003.backblazeb2.com"}),
                "key_id": ("STRING", {"default": ""}),
                "application_key": ("STRING", {"default": ""}),
                "bucket_name": ("STRING", {"default": ""}),
                "file_path": ("STRING", {"default": "path/to/image.png"}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    CATEGORY = "Cloud Storage"

    def load_image(self, endpoint_url, key_id, application_key, bucket_name, file_path):
        # Исправление endpoint
        if not endpoint_url.startswith('http'):
            endpoint_url = f'https://{endpoint_url}'

        s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=key_id,
            aws_secret_access_key=application_key
        )
        
        try:
            # Загружаем объект из B2 в память
            response = s3.get_object(Bucket=bucket_name, Key=file_path)
            file_data = response['Body'].read()
            
            # Открываем изображение через PIL
            img = Image.open(io.BytesIO(file_data))
            img = ImageOps.exif_transpose(img) # Корректный поворот (если есть EXIF)
            
            # Конвертация в RGB (для ComfyUI)
            image = img.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            
            # Создание маски (если есть альфа-канал)
            if 'A' in img.getbands():
                mask = np.array(img.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
                
            return (image, mask)
            
        except Exception as e:
            print(f"!!! Backblaze Load Error: {str(e)}")
            # В случае ошибки возвращаем пустой тензор, чтобы не "вешать" workflow
            empty_img = torch.zeros((1, 64, 64, 3))
            empty_mask = torch.zeros((1, 64, 64))
            return (empty_img, empty_mask)

NODE_CLASS_MAPPINGS = {"BackblazeLoader": BackblazeLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"BackblazeLoader": "☁️ Backblaze B2 Loader"}
