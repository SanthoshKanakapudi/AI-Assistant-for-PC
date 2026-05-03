# engine.py

import os
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import webbrowser
import functions as fun
from Config import SYSTEM_PROMPT, ROUTER_PROMPT
from PyQt6.QtCore import QThread, pyqtSignal
import time

class JarvisEngine:

    def __init__(self):

        #  Paths 
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.MEMORY_DIR = os.path.join(self.BASE_DIR, "Memory")
        os.makedirs(self.MEMORY_DIR, exist_ok=True)

        self.MAIN_FILE = os.path.join(self.MEMORY_DIR, "main_memory.txt")
        self.SESSION_FILE = os.path.join(self.MEMORY_DIR, "session_memory.txt")

        #  Load ENV 
        env_path = Path(__file__).parent / "API.env"
        load_dotenv(dotenv_path=env_path)

        self.GROQ_API_KEY = self.require_env("GROQ_API_KEY")
        self.client = Groq(api_key=self.GROQ_API_KEY)

        #  Load Functions 
        self.fns_list = self.load_functions()
        self.FUNCTION_MAP = {
            fn["name"]: getattr(fun, fn["name"])
            for fn in self.fns_list
            if hasattr(fun, fn["name"])
        }

        #  Histories 
        self.conversation_history = []
        self.router_history = []

    # Utility Methods

    def require_env(self, key):
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing environment variable: {key}")
        return value

    def load_functions(self):
        try:
            fns_path = Path(__file__).parent / "fns.json"
            if fns_path.exists():
                with open(fns_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print("Error loading fns.json:", e)
        return []

    def groq_answer(self, messages):
        try:
            ai = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages
            )
            print(ai.choices[0].message.content)
            return ai.choices[0].message.content
        except Exception as e:
            print("Groq error:", e)
            return None

    def add_to_history(self, role, content):
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > 20:
            self.conversation_history.pop(0)

    def add_to_router_history(self, role, content):
        self.router_history.append({"role": role, "content": content})
        if len(self.router_history) > 10:
            self.router_history.pop(0)

    def append_to_main(self, user_text, ai_text):
        now = datetime.now()
        time_str = now.strftime("%H:%M:%S")

        with open(self.MAIN_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n[{time_str}] USER: {user_text}\n")
            f.write(f"[{time_str}] AI: {ai_text}\n")

    # Core Chat Logic

    def chat_response(self, query):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": query})

        reply = self.groq_answer(messages)

        if reply:
            self.add_to_history("user", query)
            self.add_to_history("assistant", reply)
            self.append_to_main(query, reply)

        return reply or "I couldn't respond."
    #Execute MUltistep

    def execute_multistep(self, query, steps):
        """
        Executes steps sequentially and collects step messages
        """
        messages_to_speak = []

        for i, step in enumerate(steps):
            action = step.get("action")
            arguments = step.get("arguments", {})
            message = step.get("message")  # 🔥 NEW

            if action not in self.FUNCTION_MAP:
                return {
                    "status": "error",
                    "response": f"Invalid function: {action}"
                }

            try:
                print(f"[STEP {i+1}] {action} -> {arguments}")

                # Execute function
                self.FUNCTION_MAP[action](**arguments)
                if message:
                    messages_to_speak.append(message)

                if action == "open_app":
                    time.sleep(1.5)
                else:
                    time.sleep(0.5)

            except Exception as e:
                return {
                    "status": "error",
                    "response": f"Step {i+1} failed: {str(e)}"
                }

        return {
            "status": "success",
            "response": "Done.",
            "steps_messages": messages_to_speak
        }
    def execute_realtime(self, que):
        location = que.get("location")
        ty = que.get("type")
        # For weather in particular city - {{"type":"weather","location":"delhi"}}
        # For weather info (no city mentioned) - {{"type":"weather"}}
        # For present time of system - {{"type":"time","location":"null"}}
        # To know real time location {{"type":"null","location":"true"}}
        if ty == "weather" and location:
            data = fun.get_weather(location)
            text = "summarize following weather data " + str(data)
            self.chat_response(text)
        elif ty == "weather" and not location:
            data = fun.get_weather()
            text = "summarize following weather data " + str(data)
            self.chat_response(text)
        # elif ty == "time" and not location:
        pass


    def process_query(self, query):

        #  Router 
        router_messages = self.router_history.copy()
        router_messages.append({"role": "system", "content": ROUTER_PROMPT})
        router_messages.append({"role": "user", "content": query})

        router_reply = self.groq_answer(router_messages)

        if not router_reply:
            return {"status": "error", "response": "Router failed."}

        self.add_to_router_history("user", query)
        self.add_to_router_history("assistant", router_reply)

        try:
            router_data = json.loads(router_reply.strip())
        except json.JSONDecodeError:
            return {"status": "error", "response": "Invalid router response."}
        request_type = router_data.get("type")
        if request_type == "ai_command" and router_data.get("steps"):
            return self.chat_response(query)
        # EXECUTABLE COMMAND
        
        if request_type == "executable_command":
            action = router_data.get("action")
            arguments = router_data.get("arguments") or {}

            if action in self.FUNCTION_MAP:
                try:
                    self.FUNCTION_MAP[action](**arguments)
                    message = router_data.get("message") or "Task Done."
                    self.append_to_main(query, message)
                    return {"status": "success", "response": message}
                except Exception as e:
                    return {"status": "error", "response": f"Execution error: {str(e)}"}
            else:
                return {"status": "error", "response": "Function not allowed."}

        # WEB REQUEST
        
        elif request_type == "web_request":
            msg = router_data.get("message")
            url = router_data.get("url")
            if url:
                webbrowser.open(url)
                message = f"Opening {url}"
                self.append_to_main(query, msg)
                return {"status": "success", "response": msg}

        # AI COMMAND
        
        elif request_type == "ai_command":
            reply = self.chat_response(query)
            return {"status": "success", "response": reply}

        # MULTI STEP (Future)
        
        elif request_type == "multi_step_command":
            steps = router_data.get("steps", [])

            if not steps:
                return {"status": "error", "response": "No steps provided."}

            return self.execute_multistep(query, steps)
        
        elif request_type == "realtime_query":
            que = router_data.get("query",[])
            if not que:
                return {"status": "error", "response": "No query Provided."}
        return self.execute_realtime(que)                           
    
class EngineWorker(QThread):

    finished_signal = pyqtSignal(dict)

    def __init__(self, engine, query):
        super().__init__()
        self.engine = engine
        self.query = query

    def run(self):
        try:
            result = self.engine.process_query(self.query)
            self.finished_signal.emit(result)
        except Exception as e:
            print(e)