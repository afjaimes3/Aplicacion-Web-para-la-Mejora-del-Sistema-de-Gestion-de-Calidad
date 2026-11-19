import base64
import zlib
import json

b64_str = "i45WcvFU0lFyyU8uzU3NK8lX8MwrLsksKU3OzM9LzFGK1YlWcgsCKnDLL8pNLMkHC3j6AQVA6opKk0syyyCCASBVAUX5yakpmbmZIKOUYmMB"

try:
    compressed_data = base64.b64decode(b64_str)
    # Power BI uses Deflate (no header), so we might need -15 window size if standard zlib fails
    try:
        data = zlib.decompress(compressed_data)
    except:
        data = zlib.decompress(compressed_data, -15)
        
    print("Decoded data:", data.decode('utf-8'))
except Exception as e:
    print(f"Error decoding: {e}")
