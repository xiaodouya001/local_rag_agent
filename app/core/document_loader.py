"""
文档加载器
负责从目录加载各种格式的文档
"""

import logging
from typing import List, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_core.documents import Document

from app.exceptions import DocumentLoadError
from app.utils import sanitize_path


class DocumentLoader:
    """文档加载器"""
    
    def __init__(
        self,
        supported_file_types: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        初始化文档加载器
        
        Args:
            supported_file_types: 支持的文件类型列表，默认['.pdf', '.txt']
            logger: 日志记录器
        """
        self.supported_file_types = supported_file_types or ['.pdf', '.txt']
        self.logger = logger or logging.getLogger(__name__)
    
    def load_from_directory(
        self,
        directory: str,
        file_types: Optional[List[str]] = None
    ) -> List[Document]:
        """
        从目录加载文档
        
        Args:
            directory: 文档目录路径
            file_types: 支持的文件类型，默认使用初始化时的配置
            
        Returns:
            加载的文档列表
            
        Raises:
            DocumentLoadError: 文档加载失败
            ValueError: 目录不存在或路径无效
        """
        if file_types is None:
            file_types = self.supported_file_types
        
        # 验证和规范化路径
        try:
            base_dir = Path.cwd()
            directory_path = sanitize_path(directory, base_dir)
        except ValueError as e:
            raise ValueError(f"无效的目录路径: {e}") from e
        
        if not directory_path.exists():
            raise ValueError(f"目录不存在: {directory}")
        
        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")
        
        documents: List[Document] = []
        
        # 加载PDF文件
        if '.pdf' in file_types:
            documents.extend(self._load_pdf_files(directory_path))
        
        # 加载TXT文件
        if '.txt' in file_types:
            documents.extend(self._load_txt_files(directory_path))
        
        if not documents:
            raise DocumentLoadError(f"在目录 {directory} 中未找到任何文档")
        
        self.logger.info(f"总共加载了 {len(documents)} 个文档")
        return documents
    
    def _load_pdf_files(self, directory_path: Path) -> List[Document]:
        """加载PDF文件"""
        try:
            pdf_loader = DirectoryLoader(
                str(directory_path),
                glob="**/*.pdf",
                loader_cls=PyPDFLoader
            )
            pdf_docs = pdf_loader.load()
            self.logger.info(f"加载了 {len(pdf_docs)} 个PDF文档")
            return pdf_docs
        except Exception as e:
            error_msg = f"加载PDF文件时出错: {e}"
            self.logger.warning(error_msg, exc_info=True)
            return []
    
    def _load_txt_files(self, directory_path: Path) -> List[Document]:
        """加载TXT文件"""
        try:
            txt_loader = DirectoryLoader(
                str(directory_path),
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"}
            )
            txt_docs = txt_loader.load()
            self.logger.info(f"加载了 {len(txt_docs)} 个TXT文档")
            return txt_docs
        except UnicodeDecodeError:
            # 尝试使用其他编码
            try:
                txt_loader_utf8 = DirectoryLoader(
                    str(directory_path),
                    glob="**/*.txt",
                    loader_cls=TextLoader,
                    loader_kwargs={"encoding": "utf-8-sig"}
                )
                txt_docs = txt_loader_utf8.load()
                self.logger.info(f"使用 utf-8-sig 编码加载了 {len(txt_docs)} 个TXT文档")
                return txt_docs
            except Exception as e2:
                error_msg = f"无法加载TXT文件: {e2}"
                self.logger.error(error_msg, exc_info=True)
                return []
        except Exception as e:
            error_msg = f"加载TXT文件时出错: {e}"
            self.logger.warning(error_msg, exc_info=True)
            return []
