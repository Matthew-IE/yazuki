import json
import os
from PySide6.QtCore import QObject, Signal, QProcess, QByteArray # type: ignore

class MinecraftManager(QObject):
    status_changed = Signal(str)
    log_message = Signal(str)
    chat_received = Signal(str, str) # username, message
    error_occurred = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.handle_finished)
        
        self.node_path = "node" # Assumes node is in PATH
        self.script_path = os.path.join(os.path.dirname(__file__), "minecraft", "bot.js")

    def start_bot(self):
        if self.process.state() == QProcess.Running:
            self.stop_bot()

        # Start Node.js process
        self.process.setProgram(self.node_path)
        self.process.setArguments([self.script_path])
        self.process.start()
        
        self.status_changed.emit("Starting...")

    def stop_bot(self):
        if self.process.state() == QProcess.Running:
            self.send_command("quit")
            self.process.waitForFinished(1000)
            self.process.kill()
            self.status_changed.emit("Stopped")

    def connect_to_server(self):
        if self.process.state() != QProcess.Running:
            self.start_bot()
            # Wait a bit for process to start? 
            # Actually, we can just send the command, it will be buffered or we wait for "Ready" status.
            # But for simplicity, let's assume we can send it immediately after start or check state.
        
        options = {
            "host": self.config.get('minecraft', {}).get('host', 'localhost'),
            "port": self.config.get('minecraft', {}).get('port', 25565),
            "username": self.config.get('minecraft', {}).get('username', 'YazukiBot'),
            "auth": self.config.get('minecraft', {}).get('auth', 'offline'),
            "version": self.config.get('minecraft', {}).get('version', 'auto')
        }
        
        self.send_command("connect", {"options": options})

    def send_chat(self, message):
        self.send_command("chat", {"message": message})

    def send_command(self, command, data=None):
        if self.process.state() != QProcess.Running:
            return

        msg = {"command": command}
        if data:
            msg.update(data)
        
        json_str = json.dumps(msg) + "\n"
        self.process.write(json_str.encode('utf-8'))

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8')
        for line in data.splitlines():
            if not line.strip(): continue
            try:
                msg = json.loads(line)
                self.process_message(msg)
            except json.JSONDecodeError:
                # Raw log?
                self.log_message.emit(f"[Raw] {line}")

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8')
        self.log_message.emit(f"[Node Error] {data}")

    def handle_finished(self, exit_code, exit_status):
        self.status_changed.emit("Process Ended")

    def process_message(self, msg):
        msg_type = msg.get('type')
        data = msg.get('data')

        if msg_type == 'status':
            self.status_changed.emit(str(data))
        elif msg_type == 'info':
            self.log_message.emit(str(data))
        elif msg_type == 'error':
            self.error_occurred.emit(str(data))
        elif msg_type == 'chat':
            username = data.get('username')
            message = data.get('message')
            self.chat_received.emit(username, message)
