import re

def parse_gdrive_url(url):
    """
    Parses a Google Drive or Google Docs URL and returns a tuple:
    (is_gdrive, embed_url, detected_type, file_id)

    Supported Google Drive / Docs / Slides / Sheets / Forms URL formats:
    1. https://drive.google.com/file/d/{FILE_ID}/view?usp=sharing -> /file/d/{FILE_ID}/preview
    2. https://drive.google.com/open?id={FILE_ID} -> /file/d/{FILE_ID}/preview
    3. https://drive.google.com/uc?id={FILE_ID} -> /file/d/{FILE_ID}/preview
    4. https://docs.google.com/presentation/d/{ID}/edit -> /presentation/d/{ID}/embed
       https://docs.google.com/presentation/d/e/{PUB_ID}/pub -> /presentation/d/e/{PUB_ID}/embed
    5. https://docs.google.com/document/d/{ID}/edit -> /document/d/{ID}/preview
       https://docs.google.com/document/d/e/{PUB_ID}/pub -> /document/d/e/{PUB_ID}/pub?embedded=true
    6. https://docs.google.com/spreadsheets/d/{ID}/edit -> /spreadsheets/d/{ID}/preview
       https://docs.google.com/spreadsheets/d/e/{PUB_ID}/pubhtml -> /spreadsheets/d/e/{PUB_ID}/pubhtml?widget=true
    7. https://docs.google.com/forms/d/e/{ID}/viewform -> /forms/d/e/{ID}/viewform?embedded=true
    8. https://drive.google.com/drive/folders/{ID} -> /embeddedfolderview?id={ID}#list
    """
    if not url or not isinstance(url, str):
        return False, url or '', 'External Link', None

    clean_url = url.strip()

    # Check if Google Drive / Docs domain
    if 'drive.google.com' not in clean_url and 'docs.google.com' not in clean_url:
        return False, clean_url, 'External Link', None

    file_id = None
    file_type = 'Google Drive Resource'
    embed_url = clean_url

    # Format: Published Google Slides: docs.google.com/presentation/d/e/{PUB_ID}/...
    m_pres_pub = re.search(r'docs\.google\.com/presentation/d/e/([a-zA-Z0-9_-]+)', clean_url)
    if m_pres_pub:
        file_id = m_pres_pub.group(1)
        embed_url = f"https://docs.google.com/presentation/d/e/{file_id}/embed?start=false&loop=false&delayms=3000"
        return True, embed_url, 'Google Slides (PPT)', file_id

    # Format: Google Slides: docs.google.com/presentation/d/{ID}
    m_pres = re.search(r'docs\.google\.com/presentation/d/([a-zA-Z0-9_-]+)', clean_url)
    if m_pres and m_pres.group(1) != 'e':
        file_id = m_pres.group(1)
        embed_url = f"https://docs.google.com/presentation/d/{file_id}/embed?start=false&loop=false&delayms=3000"
        return True, embed_url, 'Google Slides (PPT)', file_id

    # Format: Published Google Document: docs.google.com/document/d/e/{PUB_ID}/...
    m_doc_pub = re.search(r'docs\.google\.com/document/d/e/([a-zA-Z0-9_-]+)', clean_url)
    if m_doc_pub:
        file_id = m_doc_pub.group(1)
        embed_url = f"https://docs.google.com/document/d/e/{file_id}/pub?embedded=true"
        return True, embed_url, 'Google Document', file_id

    # Format: Google Document: docs.google.com/document/d/{ID}
    m_doc = re.search(r'docs\.google\.com/document/d/([a-zA-Z0-9_-]+)', clean_url)
    if m_doc and m_doc.group(1) != 'e':
        file_id = m_doc.group(1)
        embed_url = f"https://docs.google.com/document/d/{file_id}/preview"
        return True, embed_url, 'Google Document', file_id

    # Format: Published Google Spreadsheet: docs.google.com/spreadsheets/d/e/{PUB_ID}/...
    m_sheet_pub = re.search(r'docs\.google\.com/spreadsheets/d/e/([a-zA-Z0-9_-]+)', clean_url)
    if m_sheet_pub:
        file_id = m_sheet_pub.group(1)
        embed_url = f"https://docs.google.com/spreadsheets/d/e/{file_id}/pubhtml?widget=true&headers=false"
        return True, embed_url, 'Google Spreadsheet', file_id

    # Format: Google Spreadsheet: docs.google.com/spreadsheets/d/{ID}
    m_sheet = re.search(r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)', clean_url)
    if m_sheet and m_sheet.group(1) != 'e':
        file_id = m_sheet.group(1)
        embed_url = f"https://docs.google.com/spreadsheets/d/{file_id}/preview"
        return True, embed_url, 'Google Spreadsheet', file_id

    # Format: Google Forms: docs.google.com/forms/d/e/{ID} or /forms/d/{ID}
    m_form = re.search(r'docs\.google\.com/forms/d/(e/)?([a-zA-Z0-9_-]+)', clean_url)
    if m_form:
        file_id = m_form.group(2)
        base_form = clean_url.split('?')[0]
        embed_url = f"{base_form}?embedded=true"
        return True, embed_url, 'Google Form', file_id

    # Format: drive.google.com/file/d/{FILE_ID}/...
    m_file = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', clean_url)
    if m_file:
        file_id = m_file.group(1)
        embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
        return True, embed_url, 'Google Drive File', file_id

    # Format: drive.google.com/open?id={FILE_ID} or /uc?id={FILE_ID}
    if 'id=' in clean_url and 'drive.google.com' in clean_url:
        m_id = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', clean_url)
        if m_id:
            file_id = m_id.group(1)
            embed_url = f"https://drive.google.com/file/d/{file_id}/preview"
            return True, embed_url, 'Google Drive File', file_id

    # Format: drive.google.com/drive/folders/{ID}
    if 'folders/' in clean_url:
        m_folder = re.search(r'folders/([a-zA-Z0-9_-]+)', clean_url)
        if m_folder:
            file_id = m_folder.group(1)
            embed_url = f"https://drive.google.com/embeddedfolderview?id={file_id}#list"
            return True, embed_url, 'Google Drive Folder', file_id

    # Fallback for any other drive.google.com or docs.google.com URL
    if '/edit' in clean_url:
        embed_url = clean_url.replace('/edit', '/preview')

    return True, embed_url, file_type, file_id

