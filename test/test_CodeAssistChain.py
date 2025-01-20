import unittest
from unittest.mock import MagicMock
from app.chain_graph.agent_state import CodeAssistState
from app.chain_graph.code_assist_chain import CodeAssistChain
# from your_module import CodeAssistWorkflow, CodeAssistState

class TestCodeAssistWorkflow(unittest.TestCase):
    def setUp(self):
        """
        테스트 준비: CodeAssistWorkflow 인스턴스 생성 및 필요한 Mock 객체 설정
        """
        self.chain = CodeAssistChain()
        # self.workflow.faiss_vector_db.search_similar_documents = MagicMock(
        #     return_value=[
        #         {'metadata': {'doc_id': 'doc1', 'original_index': 1}},
        #         {'metadata': {'doc_id': 'doc2', 'original_index': 2}}
        #     ]
        # )
        # self.workflow.es_bm25.search = MagicMock(
        #     return_value=[
        #         {'doc_id': 'doc3', 'original_index': 3},
        #         {'doc_id': 'doc4', 'original_index': 4}
        #     ]
        # )
        # self.workflow.model.invoke = MagicMock(return_value="Generated response")

    def test_context_node(self):
        """
        context_node 메서드 테스트
        """
        print("Context node output:")
        
        state = CodeAssistState()
        state['question'] = '스페인의 비는 어디에 내리나요?'
        
        self.chain.contextual_reranker(state=state, k=5)

    # def test_generate_node(self):
    #     """
    #     generate_node 메서드 테스트
    #     """
    #     state = CodeAssistState(question="Generate code for a REST API")
    #     updated_state = self.workflow.generate_node(state)
        
    #     # 결과 확인
    #     self.assertIn('response', updated_state)
    #     self.assertEqual(updated_state['response'], "Generated response")
    #     print("Generate node output:", updated_state['response'])

    # def test_run_autocode_workflow(self):
    #     """
    #     AutoCode 워크플로우 테스트
    #     """
    #     response = self.workflow.run_workflow("01", question="Write a Python function to add two numbers")
    #     self.assertEqual(response, "Generated response")
    #     print("AutoCode workflow output:", response)

    # def test_run_code_assist_workflow(self):
    #     """
    #     Code Assist 워크플로우 테스트
    #     """
    #     response = self.workflow.run_workflow("02", question="Refactor this function", current_code="def add(a, b): return a + b")
    #     self.assertEqual(response, "Generated response")
    #     print("Code Assist workflow output:", response)

    # def test_run_make_comment_workflow(self):
    #     """
    #     주석 생성 워크플로우 테스트
    #     """
    #     response = self.workflow.run_workflow("03", question="def add(a, b): return a + b")
    #     self.assertEqual(response, "Generated response")
    #     print("Make Comment workflow output:", response)

    # def test_run_mapdatautil_workflow(self):
    #     """
    #     MapDataUtil 생성 워크플로우 테스트
    #     """
    #     response = self.workflow.run_workflow("04", question="users_table")
    #     self.assertEqual(response, "Generated response")
    #     print("MapDataUtil workflow output:", response)

    # def test_run_sql_generation_workflow(self):
    #     """
    #     SQL 생성 워크플로우 테스트
    #     """
    #     response = self.workflow.run_workflow("05", question="Generate SQL for the users table", sql_request="SELECT * FROM users")
    #     self.assertEqual(response, "Generated response")
    #     print("SQL Generation workflow output:", response)

if __name__ == "__main__":
    unittest.main()
