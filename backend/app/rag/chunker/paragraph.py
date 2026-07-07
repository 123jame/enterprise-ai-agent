from app.rag.chunker.base import Chunker
from app.rag.types import Document


class ParagraphChunker(Chunker):
    """
    按段落切分文档。

    优先以空行分隔；若无段落则按单行切分。
    """

    def chunk(
        self,
        document: Document,
    ) -> list[Document]:

        paragraphs = [
            paragraph.strip()
            for paragraph in document.content.split("\n\n")
            if paragraph.strip()
        ]

        if len(paragraphs) <= 1:

            paragraphs = [
                line.strip()
                for line in document.content.splitlines()
                if line.strip()
            ]

        if not paragraphs:

            return [document]

        chunks: list[Document] = []

        for index, paragraph in enumerate(paragraphs):

            chunk_metadata = {
                **document.metadata,
                "chunk_index": index,
                "parent_id": document.id,
                "chunker": "paragraph",
            }

            chunks.append(
                Document(
                    id=f"{document.id}#{index}",
                    content=paragraph,
                    metadata=chunk_metadata,
                )
            )

        return chunks
