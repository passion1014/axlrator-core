import subprocess
import tkinter as tk
from tkinter import ttk
from threading import Thread
from time import sleep


class RAGController:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Controller")
        self.root.geometry("1000x700")

        # 버튼 영역 생성
        self.create_buttons()

        # 테이블 영역 생성
        self.create_table()

        # 출력 영역 생성
        self.create_output_area()

        # 컨테이너 상태 자동 새로고침
        self.refresh_table()

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        buttons = [
            ("Compose Up", self.compose_up),
            ("Compose Down", self.compose_down),
            ("Compose Restart", self.compose_restart),
            ("Compose Start", self.compose_start),
            ("Compose Stop", self.compose_stop),
            ("Containers", self.containers),
            ("RAG Server 시작", self.start_rag_server),
            ("로그 확인", self.show_logs),
        ]

        for name, command in buttons:
            button = tk.Button(button_frame, text=name, command=command, bg="gray", fg="white", width=15)
            button.pack(side=tk.LEFT, padx=5)

    def create_table(self):
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 테이블 생성
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("ID", "Image", "Command", "Status", "Action"),
            show="headings",
        )
        self.table.heading("ID", text="Container ID")
        self.table.heading("Image", text="Image")
        self.table.heading("Command", text="Command")
        self.table.heading("Status", text="Status")
        self.table.heading("Action", text="Action")

        self.table.column("ID", width=200)
        self.table.column("Image", width=150)
        self.table.column("Command", width=250)
        self.table.column("Status", width=100)
        self.table.column("Action", width=150)

        self.table.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_output_area(self):
        # 출력 영역 생성
        self.output_frame = tk.Frame(self.root)
        self.output_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)

        self.output_text = tk.Text(self.output_frame, height=10, wrap=tk.WORD)
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def append_output(self, text):
        """출력을 UI의 Text 위젯에 추가."""
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)

    def refresh_table(self):
        def update_table():
            while True:
                try:
                    result = subprocess.run(
                        ["docker", "ps", "-a", "--format", "{{.ID}}|{{.Image}}|{{.Command}}|{{.Status}}"],
                        capture_output=True, text=True, encoding="utf-8",
                    )
                    containers = result.stdout.strip().split("\n")

                    # 테이블 초기화
                    for row in self.table.get_children():
                        self.table.delete(row)

                    # 테이블 업데이트
                    for container in containers:
                        if container.strip():
                            values = container.split("|")

                            # 테이블에 데이터 삽입
                            item_id = self.table.insert("", tk.END, values=values)

                            # 버튼 추가
                            self.add_action_buttons(item_id, values[0])  # values[0]은 컨테이너 ID
                except Exception as e:
                    self.append_output(f"Error refreshing table: {e}")

                sleep(5)  # 5초 간격으로 업데이트

        Thread(target=update_table, daemon=True).start()
    def add_action_buttons(self, item_id, container_id):
        """특정 행에 Start 및 Stop 버튼 추가."""
        action_frame = tk.Frame(self.table)

        start_button = tk.Button(action_frame, text="Start", bg="green", fg="white", command=lambda: self.start_container(container_id))
        stop_button = tk.Button(action_frame, text="Stop", bg="red", fg="white", command=lambda: self.stop_container(container_id))

        start_button.pack(side=tk.LEFT, padx=5)
        stop_button.pack(side=tk.RIGHT, padx=5)

        self.table.item(item_id, tags=("action",))  # 테이블에 태그 추가
        self.table.tag_bind("action", "<ButtonRelease-1>", lambda e: action_frame.pack())
                            
    def start_container(self, container_id):
        """컨테이너 시작."""
        self.run_command(["docker", "start", container_id])

    def stop_container(self, container_id):
        """컨테이너 중지."""
        self.run_command(["docker", "stop", container_id])

                     
                        
    def compose_up(self):
        self.run_command(["docker-compose", "up", "-d"])

    def compose_down(self):
        self.run_command(["docker-compose", "down"])

    def compose_restart(self):
        self.compose_down()
        self.compose_up()

    def compose_start(self):
        self.run_command(["docker-compose", "start"])

    def compose_stop(self):
        self.run_command(["docker-compose", "stop"])

    def containers(self):
        self.run_command(["docker", "ps", "-a"])

    def start_rag_server(self):
        commands = [
            "python3.12 -m venv venv",
            "source venv/bin/activate",
            "pip install -r requirements.txt",
        ]
        for cmd in commands:
            self.run_command(["bash", "-c", cmd])

    def show_logs(self):
        logs = subprocess.run(
            ["docker-compose", "logs"], capture_output=True, text=True
        ).stdout

        # 팝업 창으로 로그 표시
        log_window = tk.Toplevel(self.root)
        log_window.title("Docker Logs")
        log_window.geometry("800x600")

        text_widget = tk.Text(log_window, wrap=tk.WORD)
        text_widget.insert(tk.END, logs)
        text_widget.pack(fill=tk.BOTH, expand=True)

    def run_command(self, command):
        """명령어 실행 후 출력 결과를 Text 위젯에 표시."""
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            self.append_output(result.stdout)
            if result.stderr:
                self.append_output(f"Error: {result.stderr}")
        except Exception as e:
            self.append_output(f"Error running command {command}: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RAGController(root)
    root.mainloop()
