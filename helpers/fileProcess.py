from helpers.reader import pdf, excel, image, word

def process_file(file_path: str):
    context = ""
    if file_path.endswith(".pdf"):
        context = pdf(file_path)
        print(context)
        return {"context":context}
    elif file_path.endswith(".xlsx"):
        context = excel(file_path)
        return {"context":context}
    elif file_path.endswith(".png") or file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        context = image(file_path)
        return {"context":context}
    elif file_path.endswith(".docx"):
        print(file_path)
        context = word(file_path)
        return {"context":context}
    return "Unsupported file type"


def chunk_content(content, chunk_size=1000):
    """
    Splits the content into chunks of specified size.
    
    Args:
        content (str): The content to be chunked.
        chunk_size (int): The size of each chunk.
    
    Returns:
        list: A list of content chunks.
    """
    return [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]