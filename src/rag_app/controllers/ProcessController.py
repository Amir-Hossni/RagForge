from .BaseController import BaseController
from .ProjectController import ProjectController

from pathlib import Path
from functools import partial
import asyncio
import ipaddress
import httpx
import pymupdf
import trafilatura
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..models import ProcessingEnum, ContentTypeEnum


class URLValidationError(ValueError):
    pass


class ProcessController(BaseController):
    
    def __init__(self, project_id: str):
        super().__init__()
        
        
        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)
        self.size_scale = 1048576 # convert MB to byte
        self.user_agent = "Mozilla/5.0 (compatible; rag-app/0.1)"


    def get_file_extension(self, file_id: str):
        
        # .PDF and .pdf are the same file type
        return Path(file_id).suffix.lower()
    
    
    def get_file_loader(self, file_id: str):
        
        file_ext = self.get_file_extension(file_id=file_id)
        file_path = self.project_path / file_id  
          
        if not Path(file_path).exists():
            return None  
        
        if file_ext in (ProcessingEnum.TXT.value, ProcessingEnum.MD.value):
            return partial(self.load_text_file, file_path=file_path)
          
        if file_ext in (ProcessingEnum.PDF.value, ProcessingEnum.EPUB.value):
            return partial(self.load_pymupdf_file, file_path=file_path)
        
        return None
    
    
    def get_file_content(self,file_id: str ):
        
        loader = self.get_file_loader(file_id=file_id)
        if loader:
            return loader()
        
        return None    
    
    
    def load_text_file(self, file_path: Path, encoding: str = "utf-8"):
        
        with open(file_path, encoding=encoding) as f:
            text = f.read()
            
        return [Document(page_content=text, metadata={"source": str(file_path)})]
    
    
    def load_pymupdf_file(self, file_path: Path):
        
        # pymupdf detects the format from the file, so this reads PDF and EPUB
        with pymupdf.open(str(file_path)) as doc:
            return self.get_pymupdf_documents(doc=doc, source=str(file_path))
        
        
    def get_pymupdf_documents(self, doc: pymupdf.Document, source: str):
        
        # same page_content and metadata as langchain_community PyMuPDFLoader
        pdf_metadata = {
            key: (value if value is not None else "")
            for key, value in doc.metadata.items()
        }
        
        base_metadata = {
            "producer": pdf_metadata.get("producer", ""),
            "creator": pdf_metadata.get("creator", ""),
            "creationdate": pdf_metadata.get("creationDate", ""),
            "source": source,
            "file_path": source,
            "total_pages": len(doc),
            "format": pdf_metadata.get("format", ""),
            "title": pdf_metadata.get("title", ""),
            "author": pdf_metadata.get("author", ""),
            "subject": pdf_metadata.get("subject", ""),
            "keywords": pdf_metadata.get("keywords", ""),
            "moddate": pdf_metadata.get("modDate", ""),
            "trapped": pdf_metadata.get("trapped", ""),
            "modDate": pdf_metadata.get("modDate", ""),
            "creationDate": pdf_metadata.get("creationDate", ""),
        }
        
        return [
            Document(
                page_content=page.get_text().strip(),
                metadata={**base_metadata, "page": page_number}
            )
            for page_number, page in enumerate(doc)
        ]
    
    
    @staticmethod
    async def validate_public_url(url: str):
        
        # SSRF protection: only http/https and the host must resolve to public IPs only
        parsed_url = httpx.URL(url)
        
        if parsed_url.scheme not in ("http", "https"):
            raise URLValidationError(f"Unsupported URL scheme: {parsed_url.scheme}")
        
        if not parsed_url.host:
            raise URLValidationError("URL has no host")
        
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        
        try:
            addresses = await asyncio.get_running_loop().getaddrinfo(parsed_url.host, port)
        except OSError as e:
            raise URLValidationError(f"Could not resolve host: {parsed_url.host}") from e
        
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                ip = ip.ipv4_mapped
                
            if not ip.is_global:
                raise URLValidationError(f"URL resolves to a non-public address: {ip}")
            
            
    async def fetch_url(self, url: str):
        
        # content stays in memory only, nothing is written to disk
        max_size = self.app_settings.FILE_MAX_SIZE * self.size_scale
        
        async with httpx.AsyncClient(
            timeout=self.app_settings.URL_REQUEST_TIMEOUT,
            follow_redirects=False,
            headers={"User-Agent": self.user_agent}
        ) as client:
            
            # redirects are followed manually so every hop is validated
            for _ in range(self.app_settings.URL_MAX_REDIRECTS + 1):
                await self.validate_public_url(url)
                
                async with client.stream("GET", url) as response:
                    
                    if response.is_redirect:
                        url = str(response.url.join(response.headers["location"]))
                        continue
                    
                    response.raise_for_status()
                    
                    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
                    
                    content_length = response.headers.get("content-length")
                    if content_length and content_length.isdigit() and int(content_length) > max_size:
                        raise URLValidationError("URL content exceeds the max allowed size")
                    
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > max_size:
                            raise URLValidationError("URL content exceeds the max allowed size")
                        
                    return bytes(content), content_type, response.charset_encoding, url
                
        raise URLValidationError("Too many redirects")
    
    
    def load_html_content(self, content: bytes, url: str):
        
        # trafilatura keeps the main content and removes menus, footers and ads
        result = trafilatura.bare_extraction(
            content,
            url=url,
            include_comments=False,
            include_tables=True,
            with_metadata=True
        )
        
        if result is None or not result.text:
            return []
        
        metadata = {
            "source": url,
            "title": result.title or "",
            "author": result.author or "",
            "date": result.date or "",
            "sitename": result.sitename or "",
            "description": result.description or "",
        }
        
        return [Document(page_content=result.text.strip(), metadata=metadata)]
    
    
    def load_pdf_content(self, content: bytes, url: str):
        
        with pymupdf.open(stream=content, filetype="pdf") as doc:
            return self.get_pymupdf_documents(doc=doc, source=url)
        
        
    def load_text_content(self, content: bytes, encoding: str, url: str):
        
        text = content.decode(encoding or "utf-8", errors="replace")
        
        return [Document(page_content=text, metadata={"source": url})]
    
    
    async def get_url_content(self, url: str):
        
        content, content_type, encoding, final_url = await self.fetch_url(url=url)
        
        # parsing is CPU bound, run it in a thread to keep the event loop free
        if content_type in (ContentTypeEnum.HTML.value, ContentTypeEnum.XHTML.value):
            return await asyncio.to_thread(self.load_html_content, content, final_url)
        
        if content_type == ContentTypeEnum.PDF.value:
            return await asyncio.to_thread(self.load_pdf_content, content, final_url)
        
        if content_type in (ContentTypeEnum.TXT.value, ContentTypeEnum.MD.value):
            return self.load_text_content(content, encoding, final_url)
        
        raise URLValidationError(f"Unsupported content type: {content_type}")
    
    
    def process_file_content(self, file_content: list, file_id: str,
                            chunk_size: int=100, overlap_size: int=20):
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap = overlap_size,
            length_function = len
        )
        
        file_content_text = [
            rec.page_content
            for rec in file_content
        ]
        
        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]
        
        chunks = text_splitter.create_documents(
            file_content_text,
            metadatas=file_content_metadata
            )
        
        return chunks