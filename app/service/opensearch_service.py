
_retriever = None
from app.config.setting import settings
from app.core.logger import logger

import json

import boto3
from botocore.config import Config
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

import os
from dotenv import load_dotenv
load_dotenv()

_OPENSEARCH_USERNAME = os.getenv("OPENSEARCH_USERNAME","")
_OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_PASSWORD","")
_USE_AWS_OPENSEARCH = os.getenv("USE_AWS_OPENSEARCH", "False").lower() == "true"


_MAX_CHARS = 30_000

class OpenSearchRetriever:
    def __init__(self):
        _cfg = settings.opensearch
        self.index_name = _cfg["index_name"]
        self.embedding_model = _cfg["embedding_model"]
        self.embedding_dims = _cfg["embedding_dimensions"]
        self.default_top_k = _cfg["top_k"]
        self.region = _cfg["region"]

        self._bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=self.region,
        )
        self._os_client = self._build_opensearch_client(_cfg)

    def _build_opensearch_client(self,_cfg):
        host = _cfg["host"].replace("https://","").replace("http://","")
        if _USE_AWS_OPENSEARCH:
            credentials = self._session.get_credentials()
            auth = AWSV4SignerAuth(credentials, self.region, "es")
            logger.info("OpenSearch: using SigV4 auth")
        else:
            auth = (_OPENSEARCH_USERNAME,_OPENSEARCH_PASSWORD)
            logger.info(f"OpenSearch: using basic auth (user={_OPENSEARCH_USERNAME})")

        return OpenSearch(
            hosts=[{"host":host , "port":443 }],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=60,
        )
    
    def _embed(self,text:str) ->list:
        if not text or not text.strip():
            return [0.0] * self.embedding_dims

        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS]

        payload = {
            "inputText": text,
        }

        try:
            response = self._bedrock.invoke_model(
                modelId= self.embedding_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
            result = json.loads(response["body"].read())
            if result:
                return result["embedding"]  
            else:
                return []

        except Exception as e:
            logger.error(f"Error while doing the embedding  ->{e}")
            raise

    def search(self,query:str,top_k:int=None )->list[dict]:
        top_k = top_k or self.default_top_k
        query_vector = self._embed(query)

        body = {
            "size": top_k,
            "query" : { "knn" : {"embedding" : { "vector" : query_vector, "k" : top_k }}},
            "_source": { "excludes" : ["embedding"]},
        }

        repsonse = self._os_client.search(index=self.index_name, body=body)

        hits = repsonse["hits"]["hits"]
        results = []
        for hit in hits:
            src = hit["_source"]
            results.append({
                "content":src.get("content",""),
                "score": hit["_score"],
                "file_name" : src.get("file_name",""),
                "source_key": src.get("source_key",""),
                "file_type":src.get("file_type", ""),
                "chunk_index":src.get("chunk_index",0),
                "total_chunks":src.get("total_chunks",0)
            })
        logger.info(f"Opensearch returned{len(results)} chunks for query")
        return results


def get_retriever()->OpenSearchRetriever:
    global _retriever
    if _retriever is None:
        _retriever = OpenSearchRetriever()
    return _retriever