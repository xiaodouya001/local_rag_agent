"""
文档加载器
负责从目录加载各种格式的文档
"""

import logging
from pathlib import Path
import tempfile

from langchain_community.document_loaders import DirectoryLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from app.core.utils.common import sanitize_path
from app.infrastructure import DocumentLoadError


class DocumentLoader:
    """文档加载器"""

    def __init__(self,
                 supported_file_types: list[str] | None = None,
                 logger: logging.Logger | None = None):
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
            file_types: list[str] | None = None,
            allow_temp_dir: bool = False) -> list[Document]:
        """
        从目录加载文档

        Args:
            directory: 文档目录路径
            file_types: 支持的文件类型，默认使用初始化时的配置
            allow_temp_dir: 是否允许临时目录（用于文件上传等场景）

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
            directory_path = Path(directory).resolve()

            # 检查是否是临时目录
            is_temp_dir = False
            if allow_temp_dir:
                temp_dir = Path(tempfile.gettempdir()).resolve()
                try:
                    directory_path.relative_to(temp_dir)
                    is_temp_dir = True
                    self.logger.debug(f"检测到临时目录: {directory_path}")
                except ValueError:
                    # 不是系统临时目录，继续检查
                    pass

            # 如果不是临时目录，进行路径安全检查
            if not is_temp_dir:
                base_dir = Path.cwd()
                directory_path = sanitize_path(directory, base_dir)
        except ValueError as e:
            raise ValueError(f"无效的目录路径: {e}") from e

        if not directory_path.exists():
            raise ValueError(f"目录不存在: {directory}")

        if not directory_path.is_dir():
            raise ValueError(f"路径不是目录: {directory}")

        documents: list[Document] = []

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

    def _load_pdf_files(self, directory_path: Path) -> list[Document]:
        """加载PDF文件"""
        try:
            pdf_loader = DirectoryLoader(str(directory_path),
                                         glob="**/*.pdf",
                                         loader_cls=PyPDFLoader)
            pdf_docs = pdf_loader.load()

            # 为每个文档添加详细的 metadata
            for doc in pdf_docs:
                self._enhance_metadata(doc, directory_path)

            self.logger.info(f"加载了 {len(pdf_docs)} 个PDF文档")
            return pdf_docs
        except Exception as e:
            error_msg = f"加载PDF文件时出错: {e}"
            self.logger.warning(error_msg, exc_info=True)
            return []

    def _load_txt_files(self, directory_path: Path) -> list[Document]:
        """加载TXT文件"""
        try:
            txt_loader = DirectoryLoader(str(directory_path),
                                         glob="**/*.txt",
                                         loader_cls=TextLoader,
                                         loader_kwargs={"encoding": "utf-8"})
            txt_docs = txt_loader.load()

            # 为每个文档添加详细的 metadata
            for doc in txt_docs:
                self._enhance_metadata(doc, directory_path)

            self.logger.info(f"加载了 {len(txt_docs)} 个TXT文档")
            return txt_docs
        except UnicodeDecodeError:
            # 尝试使用其他编码
            try:
                txt_loader_utf8 = DirectoryLoader(
                    str(directory_path),
                    glob="**/*.txt",
                    loader_cls=TextLoader,
                    loader_kwargs={"encoding": "utf-8-sig"})
                txt_docs = txt_loader_utf8.load()

                # 为每个文档添加详细的 metadata
                for doc in txt_docs:
                    self._enhance_metadata(doc, directory_path)

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

    def _enhance_metadata(self, doc: Document, base_dir: Path) -> None:
        """
        增强文档的 metadata，添加文件名、修改时间等信息

        Args:
            doc: 文档对象
            base_dir: 基础目录路径
        """
        from pathlib import Path

        source = doc.metadata.get('source', '')
        if not source:
            return

        try:
            file_path = Path(source)
            if not file_path.is_absolute():
                file_path = base_dir / file_path

            if file_path.exists():
                # 获取文件信息
                stat = file_path.stat()

                # 提取文件名（不含路径）
                filename = file_path.name

                # 添加或更新 metadata
                doc.metadata['filename'] = filename
                doc.metadata['file_path'] = str(file_path.resolve())
                doc.metadata['file_size'] = stat.st_size
                doc.metadata['modified_time'] = stat.st_mtime
                doc.metadata['file_hash'] = f"{filename}_{stat.st_mtime}_{stat.st_size}"
        except Exception as e:
            self.logger.debug(f"无法增强文档 metadata ({source}): {e}")
