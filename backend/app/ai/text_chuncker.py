from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

class TextChunker:
    
    def __init__(
        self,
        chunk_size : int,
        chunk_overlap : int
    ):
        self.chunk_size = chunk_size
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size = chunk_size,
            chunk_overlap = chunk_overlap
        )    
        
    def split(
        self,
        documents: list[Document]
    )->list[Document]:
        
        chunks = []
        pending_text = []
        current_page = None
        document_id = None
        
        def flush_text():
            if not pending_text:
                return
            
            combined_text = "\n\n".join(pending_text)
            
            document = Document(
                page_content=combined_text,
                metadata={
                    "document_id":document_id,
                    "page" : current_page,
                    "image_ids" :[],
                    "content_type" : "text"
                }
            )
            
            chunks.extend(
                self.splitter.split_documents([document])
            )
            
            pending_text.clear()
            
        for document in documents:
            page = document.metadata["page"]
            document_id = document.metadata["document_id"]
            
            is_image = (
                document.metadata.get("content_type") == "image"
            )
            
            if current_page is not None and page != current_page:
                flush_text()
            
            current_page = page
            
            if is_image:
                flush_text()
                
                chunks.append(document)
                continue
                 
            combined_size = sum(
                len(text) for text in pending_text
            )
            
            if combined_size + len(document.page_content) > self.chunk_size:
                flush_text()

            pending_text.append(document.page_content)
                
        flush_text()
        
        return chunks
            
