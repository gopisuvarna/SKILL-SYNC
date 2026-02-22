import uuid
from supabase import create_client
from django.conf import settings

supabase = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

def upload_pdf_to_supabase(file, filename):
    unique_filename = f"{uuid.uuid4()}_{filename}"

    supabase.storage.from_("resumes").upload(
        path=f"pdfs/{unique_filename}",
        file=file.read(),
        file_options={"content-type": "application/pdf"},
    )

    file_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/resumes/pdfs/{unique_filename}"
    
    return file_url
