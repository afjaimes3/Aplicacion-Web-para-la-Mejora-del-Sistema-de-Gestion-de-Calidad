
from mailmerge import MailMerge

template = "plantilla.docx"
try:
    document = MailMerge(template)
    print("Fields in template:")
    for field in sorted(document.get_merge_fields()):
        print(field)
except Exception as e:
    print(f"Error: {e}")
