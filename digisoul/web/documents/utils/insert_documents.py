# 将文档插入到向量数据库当中

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from web.documents.utils.custom_embeddings import CustomEmbeddings
import lancedb
from langchain_community.vectorstores import LanceDB

# 调用百炼平台的 embedding 模型，将文本内容转化为向量，并写入向量数据库当中
def insert_documents():
    loader = TextLoader('web/documents/data/data.txt')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    print(f'已切分成 {len(texts)} 个文本')

    embeddings = CustomEmbeddings()
    db = lancedb.connect('web/documents/db/lancedb_storage')
    vector_db = LanceDB.from_documents(
        documents=texts,
        embedding=embeddings,
        connection=db,
        table_name='my_knowledge_base',
        mode='overwrite',
    )
    print(f'已插入 {vector_db._table.count_rows()} 数据')
