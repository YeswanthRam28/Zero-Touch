from pathlib import Path
p = Path('test_upload.png')
p.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR')
print('wrote', p.resolve())
