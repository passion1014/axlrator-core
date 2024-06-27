from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

def list_todo(state: GraphState) -> GraphState:
    goal = state["goal"]
    # 리스트 작성
    todo = create_todo_list(goal)
    # 할 일 목록을 포맷팅
    todo = format_task(create_todo_list(todo))
    return GraphState(todo=todo)


def start_job(state: GraphState) -> GraphState:
    todo = state["todo"]
    if len(todo):
        current_job, total_time = todo.pop(0)
        status = "진행중"
        time_spent = 0
    return GraphState(
        current_job=current_job,
        total_time=total_time,
        status=status,
        time_spent=time_spent,
    )


def process_job(state: GraphState) -> GraphState:
    time_spent = state["time_spent"]
    time_spent += 1

    return GraphState(time_spent=time_spent)


def check_progress(state: GraphState) -> GraphState:
    if state["time_spent"] >= state["total_time"]:
        status = "다음 작업"
        if len(state["todo"]) == 0:
            status = "종료"
    else:
        status = "진행중"
    return GraphState(status=status)


def next_step(state: GraphState) -> GraphState:
    return state["status"]



# langgraph.graph에서 StateGraph와 END를 가져옵니다.
workflow = StateGraph(GraphState)

# Todo 를 작성합니다.
workflow.add_node("list_todo", list_todo)  # 에이전트 노드를 추가합니다.

# Todo 작업을 시작합니다.
workflow.add_node("start_job", start_job)

# 작업을 진행합니다.
workflow.add_node("process_job", process_job)

# 작업을 중간 체크합니다.
workflow.add_node("check_progress", check_progress)

# 각 노드들을 연결합니다.
workflow.add_edge("list_todo", "start_job")
workflow.add_edge("start_job", "process_job")
workflow.add_edge("process_job", "check_progress")

# 조건부 엣지를 추가합니다.
workflow.add_conditional_edges(
    "check_progress",  # 관련성 체크 노드에서 나온 결과를 is_relevant 함수에 전달합니다.
    next_step,
    {
        "진행중": "process_job",  # 관련성이 있으면 종료합니다.
        "다음 작업": "start_job",  # 관련성이 없으면 다시 답변을 생성합니다.
        "종료": END,  # 관련성 체크 결과가 모호하다면 다시 답변을 생성합니다.
    },
)

# 시작점을 설정합니다.
workflow.set_entry_point("list_todo")

# 기록을 위한 메모리 저장소를 설정합니다.
memory = MemorySaver()

# 그래프를 컴파일합니다.
app = workflow.compile(checkpointer=memory)
