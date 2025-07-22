from typing import Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from axlrator_core.chain_graph.agent_state import AgentState, CodeAssistAutoCompletion, CodeAssistChatState, CodeAssistState
from axlrator_core.chain_graph.code_chat_agent import store_vector_sources
from axlrator_core.common.code_assist_utils import extract_code_blocks
from axlrator_core.common.string_utils import is_table_name
from axlrator_core.db_model.data_repository import RSrcTableColumnRepository, RSrcTableRepository, ChunkedDataRepository
from axlrator_core.process.reranker import get_reranker
from langgraph.graph import StateGraph, END
from axlrator_core.utils import get_llm_model
from axlrator_core.vectordb.bm25_search import ElasticsearchBM25
from langfuse.callback import CallbackHandler
from langgraph.types import StreamWriter
from langfuse import Langfuse


import logging

from axlrator_core.vectordb.vector_store import get_vector_store


class DocumentManualChain:
    def __init__(self, session, index_name:str="manual_document"):
        self.index_name = index_name
        self.db_session = session
        self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])
        self.langfuse = Langfuse()

    @staticmethod
    def get_last_user_message(state: CodeAssistState) -> Optional[str]:
        """
        Retrieves the last message from the user (HumanMessage) in the chat history.
        
        Returns:
            The content of the last HumanMessage, or None if not found.
        """
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                return msg.content.strip()
        return None

    @staticmethod
    def format_chat_history(state: CodeAssistState) -> str:
        """
        Formats the chat history for display, ensuring proper indentation and separation.
        """
        chat_lines = []
        indent = "  "
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                chat_lines.append(f"{indent}USER: {msg.content.strip()}")
            elif isinstance(msg, AIMessage):
                chat_lines.append(f"{indent}ASSISTANT: {msg.content.strip()}")
        # Join messages with a blank line for separation
        chat_history = "<chat_history>\n" + "\n\n".join(chat_lines) + "\n</chat_history>"
        return chat_history


    async def contextual_reranker(self, state: CodeAssistState, k: int=10, semantic_weight: float = 0.8, bm25_weight: float = 0.2) -> CodeAssistState:
        question = state['question']

        # VectorDB 조회
        vector_store = get_vector_store(collection_name=self.index_name)
        semantic_results = vector_store.similarity_search_with_score(query=question, k=3) 


        # 조회된 청크가 작을 경우 체크하여 보완한다.
        for doc in semantic_results:
            _content = doc.get("content")
            _chunked_data_id = doc.get("chunked_data_id")
            _doc_id = doc.get("doc_id")
            if _content and _chunked_data_id:
                expanded_content = await self.check_need_next_chunk(query=question, doc_id=_doc_id, chunked_data_id=_chunked_data_id, context=_content)
                doc["content"] = expanded_content


        # webui에 인용정보를 보여주기 위하여 저장한다
        # 현재는 bm25를 조회하지 않으므로 여기서 셋팅, 추후는 bm25데이터도 고려해서 셋팅해야 함
        if semantic_results:
            store_vector_sources(state.get("metadata"), semantic_results, semantic_results)

        
        # BM25 조회
        bm25_results = self.es_bm25.search(query=question, k=2) # elasticsearch 조회
        
        logging.info("## Step1. Semantic Results: %s", semantic_results)
        logging.info("## Step1. BM25 Results: %s", bm25_results)

        # VectorDB의 doc_id, original_index값 추출
        ranked_chunk_ids = [
            (
                result['id'],
                result.get('metadata', {}).get('chunked_data_id', None) # chunked_data_id
            )
            for result in semantic_results
            if 'id' in result
        ]

        # BM25조회 결과의 doc_id, original_index값 추출
        ranked_bm25_chunk_ids = [
            (
                result['doc_id'], 
                result['original_index'] # chunked_data_id
            ) 
            for result in bm25_results
        ]
        
        # 2개의 결과를 머지 (중복제거)
        chunk_ids = list(set(ranked_chunk_ids + ranked_bm25_chunk_ids))

        # 스코어 계산 및 랭크퓨전 (RRF와 유사함)
        chunk_id_to_score = {}
        for chunk_id in chunk_ids:
            score = 0
            if chunk_id in ranked_chunk_ids:
                score += semantic_weight * (1 / (ranked_chunk_ids.index(chunk_id) + 1))
            if chunk_id in ranked_bm25_chunk_ids:
                score += bm25_weight * (1 / (ranked_bm25_chunk_ids.index(chunk_id) + 1))
            chunk_id_to_score[chunk_id] = score
            
        # 정렬 (score, chunk_id의 1번째, chunk_id의 2번째)
        sorted_chunk_ids = sorted(
            chunk_id_to_score.keys(), 
            key=lambda x: (chunk_id_to_score[x], x[0], x[1]), 
            reverse=True
        )
        logging.info("### Step2. 랭크퓨전 결과 (sorted_chunk_ids) : %s", sorted_chunk_ids)
        
        # docid와 content/value를 매핑한 딕셔너리 생성
        # semantic_docid_to_content = {result['vector_index']: result['content'] for result in semantic_results}
        # bm25_docid_to_value = {result['doc_id']: result['content'] for result in bm25_results}
        
        # docid와 content/value를 매핑한 딕셔너리 생성
        semantic_docid_to_content = {
            (
                result['id'], 
                result.get('metadata', {}).get('chunked_data_id', None) # chunked_data_id
            ): result['content']
            for result in semantic_results
        }
        bm25_docid_to_value = {
            (
                result.get('doc_id', None),
                result.get('original_index', None)
            ): result.get('content', '')
            for result in bm25_results
        }

        # 리랭킹 하기 전 정렬된 데이터 리스트
        sorted_documents = [{
            'score': chunk_id_to_score[chunk_id],
            'from_semantic': chunk_id in ranked_chunk_ids,
            'from_bm25': chunk_id in ranked_bm25_chunk_ids,
            'chunked_data_id': (
                chunk_id[1] if chunk_id in ranked_chunk_ids
                else chunk_id[1] if chunk_id in ranked_bm25_chunk_ids
                else ''
            ),
            'content': (
                semantic_docid_to_content.get(chunk_id, '') if chunk_id in ranked_chunk_ids
                else bm25_docid_to_value.get(chunk_id, '') if chunk_id in ranked_bm25_chunk_ids
                else ''
            )
        } for chunk_id in sorted_chunk_ids[:k]]
        
        logging.info("### Step3. 머지/정렬된 결과(sorted_documents) : %s", sorted_documents)
        
        # 리랭킹
        valid_documents = [doc for doc in sorted_documents if doc['content']]
        reranker = get_reranker()
        reranker.cross_encoder(query=question, documents=valid_documents)

        state['context'] = [doc['content'] for doc in valid_documents]

        return state

    def search_similar_context(self, state: AgentState) -> AgentState:
        enriched_query = state['question']
        
        vector_store = get_vector_store(collection_name=self.index_name)
        docs = vector_store.similarity_search_with_score(query=enriched_query, k=2) 
        
        # state['context'] = "\n".join(doc['content'] for doc in docs)
        state['context'] = combine_documents_with_relevance(docs)
        return state

    def get_table_desc(self, state: AgentState) -> AgentState:
        context = state['question']
        table_json = {}
        table_names = context.split(',')
        
        rsrc_table_repo = RSrcTableRepository(session=self.db_session)
        rsrc_table_column_repo = RSrcTableColumnRepository(session=self.db_session)

        for table_name in table_names:
            if table_name.strip():
                table_data = rsrc_table_repo.get_data_by_table_name(table_name=table_name.strip())
                for table in table_data:
                    columns = rsrc_table_column_repo.get_data_by_table_id(rsrc_table_id=table.id)
                    column_jsons = [{
                        'name': column.column_name,
                        'type': column.column_type,
                        'desc': column.column_desc.strip()
                    } for column in columns]

                    table_json[table_name.strip()] = {
                        'table_name': table_name.strip(),
                        'columns': column_jsons
                    }

        state['context'] = table_json
        return state

    def generate_response_astream(self, state: CodeAssistState, writer: StreamWriter) -> CodeAssistChatState:
        prompt = state['prompt']
        response = self.model.invoke(prompt)

        # AIMessage 객체에서 텍스트 콘텐츠 추출
        state['response'] = response.content if hasattr(response, 'content') else str(response)

        return state
    
    def choose_prompt_for_task(self, state: CodeAssistState) -> CodeAssistState:
        langfuse_prompt = self.langfuse.get_prompt("AXL_MANUAL_DOC_QUERY")
        state['prompt'] = langfuse_prompt.compile(
            reference=state['context'],
            query=state['question'],
        )
        return state

    def chain_manual_query(self) -> CodeAssistState:
        '''
        메뉴얼 질문
        '''
        graph = StateGraph(CodeAssistState)
        graph.add_node("contextual_reranker", self.contextual_reranker) # hybrid cotext search
        # graph.add_node("search_similar_context", self.search_similar_context) # 컨텍스트 정보 조회
        graph.add_node("choose_prompt_for_task", self.choose_prompt_for_task) # 프롬프트 선택
        graph.add_node("generate_response_astream", self.generate_response_astream) # 모델호출
        
        graph.set_entry_point("contextual_reranker")    
        graph.add_edge("contextual_reranker", "choose_prompt_for_task")
        graph.add_edge("choose_prompt_for_task", "generate_response_astream")
        graph.add_edge("generate_response_astream", END)

        chain = graph.compile() # CompiledStateGraph
        chain.with_config(callbacks=[CallbackHandler()])
        
        return chain

    async def check_need_next_chunk(self, query: str, doc_id:str, chunked_data_id:int, context: str):
        prompt = f"""The following context is from a vector database. Decide if it is enough to answer the question.

- If earlier context is needed: [front]  
- If later context is needed: [back]  
- If both are needed: [both]  
- If the context is enough: [enough]

Context:
{context}

Question:
{query}

Answer with one of: [front], [back], [both], [enough]
"""
        result = self.model.invoke([HumanMessage(content=prompt)])
        answer = result.content.strip()
        answer = answer.lower()

        chunkedDataRepository = ChunkedDataRepository(session=self.db_session)

        iDoc_id = int(doc_id)
        iChunked_data_id = int(chunked_data_id)
        
        if "front" in answer:
            before_chunk_id = iChunked_data_id - 1
            before_data = await chunkedDataRepository.get_by_resrc_id_and_chunk_id(org_resrc_id=iDoc_id, id=before_chunk_id)
            before = before_data.content if before_data and before_data.content else ""
            context = f"{before}\n{context}"
            return context
            
        elif "back" in answer:
            after_chunk_id = iChunked_data_id + 1
            after_data = await chunkedDataRepository.get_by_resrc_id_and_chunk_id(org_resrc_id=iDoc_id, id=after_chunk_id)
            after = after_data.content if after_data and after_data.content else ""
            context = f"{context}\n{after}"
            return context
        
        elif "both" in answer:
            after_chunk_id = iChunked_data_id + 1
            after_data = await chunkedDataRepository.get_by_resrc_id_and_chunk_id(org_resrc_id=iDoc_id, id=after_chunk_id)

            before_chunk_id = iChunked_data_id - 1
            before_data = await chunkedDataRepository.get_by_resrc_id_and_chunk_id(org_resrc_id=iDoc_id, id=before_chunk_id)

            before = before_data.content if before_data and before_data.content else ""
            after = after_data.content if after_data and after_data.content else ""
            context = f"{before}\n{context}\n{after}"
            return context

        return context




# Helper function: combine_documents_with_relevance
def combine_documents_with_relevance(docs):
    # combined_context = "\n".join([doc['content'] for doc in docs])
    if not docs:
        return ""

    combined_context = []
    for doc in docs[:2]:  # 앞에서 2개의 항목만 사용
        if doc['content'] not in combined_context:  # 중복 제거
            combined_context.append(doc['content'])

    return "\n".join(combined_context)



from langchain_core.prompts import PromptTemplate

def combine_documents_with_next_content(docs) -> list:
    if not docs:
        return ""

    model = get_llm_model()
    callback_handler = CallbackHandler()
    
    '''
    다음 두 문장은 서로 연결되어 하나의 문장처럼 읽히나요?
    문장1: {{chunk}}
    문장2: {{next_chunk}}

    응답은 'YES' 또는 'NO'로만 답변하세요.
    '''
    # TODO: 2개 문장의 컨텍스트가 연결되어 있는지 확인하도록 프롬프트 수정해야 됨
    # max token 을 체크하여서 문장이 너무 길면 문장을 잘라야 함
    langfuse_prompt = Langfuse().get_prompt("AXL_CHECK_MERGE_CONTEXT")

    merged_chunks = []
    buffer = ""

    i = 0
    while i < len(docs):
        current = docs[i].strip()
        if not buffer:
            buffer = current
        else:
            buffer = f"{buffer} {current}"

        should_merge = False
        if i + 1 < len(docs):
            next_content = docs[i + 1].strip()
            prompt = langfuse_prompt.compile(
                chunk=buffer,
                next_chunk=next_content,
            )
            response = model.invoke(prompt)
            answer = response.content.strip().lower()
            if "YES" in answer.upper():
                buffer = f"{buffer} {next_content}"
                i += 2  # 다음 항목도 같이 사용했으므로 2개 스킵
                merged_chunks.append(buffer)
                buffer = ""
                continue
            else:
                should_merge = True
        else:
            should_merge = True

        if should_merge:
            merged_chunks.append(buffer)
            buffer = ""
            i += 1
            continue

    if buffer:
        merged_chunks.append(buffer)

    return merged_chunks
