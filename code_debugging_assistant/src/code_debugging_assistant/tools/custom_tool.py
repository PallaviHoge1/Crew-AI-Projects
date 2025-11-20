# custom_tool.py
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from crewai import Agent

# -----------------------
# Tool input schemas
# -----------------------
class MyCustomToolInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="Description of the argument.")

class LocalPythonToolInput(BaseModel):
    """Input schema for LocalPythonTool."""
    code: str = Field(..., description="Python source code to execute/check.")

# -----------------------
# Tools
# -----------------------
class MyCustomTool(BaseTool):
    name: str = "my_custom_tool"
    description: str = (
        "Clear description for what this tool is useful for. Your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = MyCustomToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "example tool output"

class LocalPythonTool(BaseTool):
    """
    A simple local python runner / syntax checker.
    This implements _run and accepts an argument 'code' as per args_schema.
    NOTE: This runs code with exec() — in production you must sandbox carefully.
    """
    name: str = "local_python_tool"
    description: str = "Run/validate small python snippets locally (for syntax/runtime checks)."
    args_schema: Type[BaseModel] = LocalPythonToolInput

    def _run(self, code: str) -> Dict[str, Any]:
        try:
            # Try to compile first to detect syntax / indentation errors without executing
            compile(code, "<string>", "exec")
        except Exception as e:
            return {"success": False, "stage": "compile", "error": repr(e)}
        # If compile succeeded, optionally exec in a minimal namespace
        ns = {}
        try:
            exec(code, {"__name__": "__main__"}, ns)
            return {"success": True, "stage": "exec", "namespace_keys": list(ns.keys())}
        except Exception as e:
            return {"success": False, "stage": "exec", "error": repr(e)}

# -----------------------
# Helper: lightweight LLM-call wrapper
# -----------------------
def default_llm_call(prompt: str, max_tokens: int = 512) -> str:
    """
    Default fallback when you don't have an LLM configured.
    Replace this with your crewai/OpenAI call (e.g., self.llm.call(...) or similar).
    """
    # Very small rule-based analyzer for demo purposes:
    if "Analyze the following Python function" in prompt:
        if "IndentationError" in prompt or "if n < 0:" in prompt and "\n    " not in prompt:
            return "- IndentationError: function body not indented\n- Missing handling for n==0\n- Suggest adding type checks and docstring"
        return "- No syntax errors found (quick heuristic)."
    if "produce corrected Python code" in prompt:
        # Return a safe corrected fibonacci function (short)
        return (
            "def fibonacci_iterative(n: int) -> list:\n"
            "    \"\"\"Return first n Fibonacci numbers. n <= 0 -> []\"\"\"\n"
            "    if not isinstance(n, int):\n"
            "        raise TypeError('n must be int')\n"
            "    if n <= 0:\n"
            "        return []\n"
            "    if n == 1:\n"
            "        return [0]\n"
            "    fib_sequence = [0, 1]\n"
            "    while len(fib_sequence) < n:\n"
            "        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])\n"
            "    return fib_sequence\n"
        )
    return "LLM fallback: no detailed analysis available."

# -----------------------
# Agents
# -----------------------
class CodeAnalyzer(Agent):
    """
    Agent to analyze code for syntax and logic issues.
    If you have a real crewai LLM bound to Agent, replace the llm_call usage
    below with your Agent's LLM method (e.g., self.call_llm(...) or self.llm.call(...)).
    """
    def llm_call(self, prompt: str, max_tokens: int = 512) -> str:
        # If the Agent base provides an LLM client, use it here.
        # Example (pseudo): return self.llm.call(prompt, max_tokens=max_tokens)
        # But to keep this file runnable without external LLM, use fallback:
        return default_llm_call(prompt, max_tokens=max_tokens)

    def run(self, code_text: str) -> Dict[str, Any]:
        prompt = f"Analyze the following Python function for syntax and logical errors. Output a short bullet list.\n\n{code_text}"
        analysis = self.llm_call(prompt=prompt, max_tokens=256)

        # Use LocalPythonTool to get quick compile/exec feedback (direct instantiation)
        python_tool = LocalPythonTool()
        runtime_check = python_tool._run(code=code_text)
        return {"analysis": analysis, "runtime_check": runtime_check}

class CodeCorrector(Agent):
    def llm_call(self, prompt: str, max_tokens: int = 512) -> str:
        return default_llm_call(prompt, max_tokens=max_tokens)

    def run(self, code_text: str, analysis: Any) -> Dict[str, str]:
        prompt = (
            "Using the analysis below, produce corrected Python code. "
            "Return only the corrected code block (no extra text).\n\n"
            f"Analysis:\n{analysis}\n\nCode:\n{code_text}"
        )
        corrected = self.llm_call(prompt=prompt, max_tokens=600)
        return {"corrected_code": corrected}

class Manager(Agent):
    """
    Manager coordinates the Analyzer and Corrector.
    Note: Agent base expects fields like name, role, goal, backstory when instantiated.
    """
    def run(self, code_text: str):
        # Create agents with required pydantic fields (role, goal, backstory)
        analyzer = CodeAnalyzer(name="Analyzer", role="analyze", goal="find code issues", backstory="Static analyzer agent")
        correction_agent = CodeCorrector(name="Corrector", role="correct", goal="fix code issues", backstory="Code fix agent")

        # Run analysis
        analysis_res = analyzer.run(code_text)
        # Run correction using analysis text (here we pass LLM analysis string)
        corrected = correction_agent.run(code_text, analysis_res["analysis"])

        # sanity check the corrected code with LocalPythonTool
        python_tool = LocalPythonTool()
        final_run = python_tool._run(code=corrected["corrected_code"])
        return {"analysis": analysis_res, "corrected": corrected, "final_run": final_run}

# -----------------------
# Example usage (runnable)
# -----------------------
if __name__ == "__main__":
    sample_code = '''def fibonacci_iterative(n):
                    if n < 0:
                    return []
                    elif n == 1:
                    return [0]
                    elif n == 2:
                    return [0, 1]
                    fib_sequence = [0, 1]
                    for i in range(2, n):
                    next_fib = fib_sequence[-1] + fib_sequence[-2]
                    fib_sequence.append(next_fib)
                    return fib_sequence
                    '''

    # IMPORTANT: include required fields role, goal, backstory when creating Manager
    mgr = Manager(name="Manager", role="manage", goal="coordinate analyzer and corrector", backstory="Oversees code analysis/correction")
    out = mgr.run(sample_code)

    print("ANALYSIS (LLM):", out["analysis"]["analysis"])
    print("RUNTIME CHECK (Analyzer's compile/exec stage):", out["analysis"]["runtime_check"])
    print("\nCORRECTED CODE:\n", out["corrected"]["corrected_code"])
    print("\nFINAL RUN (after correction):", out["final_run"])
