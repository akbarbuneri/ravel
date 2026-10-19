"""Child process that executes one untrusted harness.

Launched by ravel.sandbox inside `unshare -rn` (no network), with resource limits, restricted
builtins and an import allow-list. All tool and LLM access goes through a JSON-lines RPC over
stdin/stdout; the parent brokers, meters and logs every call. This is a research isolation layer,
not a hardened security boundary.
"""
import builtins
import json
import resource
import signal
import sys

PROTO_OUT = sys.stdout
sys.stdout = sys.stderr  # harness prints cannot corrupt the protocol

ALLOWED_MODULES = {"re", "math", "json", "statistics", "collections", "itertools", "functools",
                   "string", "decimal", "fractions", "difflib", "unicodedata", "typing"}
SAFE_BUILTINS = {k: getattr(builtins, k) for k in (
    "abs all any bool dict enumerate filter float format frozenset int isinstance issubclass iter len "
    "list map max min next print range repr reversed round set slice sorted str sum tuple zip "
    "Exception ValueError KeyError IndexError TypeError RuntimeError ZeroDivisionError StopIteration "
    "AttributeError ArithmeticError LookupError NotImplementedError True False None hasattr callable chr ord divmod pow"
).split() if hasattr(builtins, k)}


def _limited_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".")[0] not in ALLOWED_MODULES:
        raise ImportError(f"import of {name!r} is not permitted in the harness sandbox")
    return builtins.__import__(name, globals, locals, fromlist, level)


SAFE_BUILTINS["__import__"] = _limited_import
SAFE_BUILTINS["__build_class__"] = builtins.__build_class__


class ToolError(Exception):
    pass


class HarnessTimeout(BaseException):
    pass


def _send(msg):
    PROTO_OUT.write(json.dumps(msg) + "\n")
    PROTO_OUT.flush()


def _recv():
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return json.loads(line)


def _rpc(tool, *args, **kwargs):
    _send({"type": "call", "tool": tool, "args": list(args), "kwargs": kwargs})
    r = _recv()
    if not r.get("ok"):
        raise ToolError(r.get("error", "tool error"))
    return r["result"]


class Tools:
    """Capabilities available to a harness. Every method is brokered by the parent process."""
    ToolError = ToolError

    def llm(self, prompt, max_tokens=256, system=None):
        return _rpc("llm", str(prompt), max_tokens=int(max_tokens), system=system)

    def search(self, query, k=4):
        return _rpc("search", str(query), k=int(k))

    def lookup_ticker(self, name):
        return _rpc("lookup_ticker", str(name))

    def get_financials(self, ticker, metric, period):
        return _rpc("get_financials", str(ticker), str(metric), str(period))

    def calculator(self, expression):
        return _rpc("calculator", str(expression))

    def is_authorized(self, account_id):
        return _rpc("is_authorized", str(account_id))

    def get_portfolio(self, account_id):
        return _rpc("get_portfolio", str(account_id))


def _alarm(signum, frame):
    raise HarnessTimeout()


def main():
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 ** 3, 2 * 1024 ** 3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (900, 900))
    cfg = _recv()
    ns = {"__builtins__": SAFE_BUILTINS, "__name__": "harness", "ToolError": ToolError}
    try:
        exec(compile(cfg["code"], "harness.py", "exec"), ns)
        run = ns["run"]
        assert callable(run)
        _send({"type": "ready"})
    except BaseException as e:  # noqa: BLE001 - report any load failure
        _send({"type": "load_error", "error": f"{type(e).__name__}: {e}"[:400]})
        return
    signal.signal(signal.SIGALRM, _alarm)
    tools = Tools()
    while True:
        job = _recv()
        signal.alarm(int(cfg.get("timeout", 90)))
        try:
            ans = run(job["question"], tools)
            _send({"type": "done", "answer": "" if ans is None else str(ans)[:2000], "error": None})
        except HarnessTimeout:
            _send({"type": "done", "answer": "", "error": "timeout"})
        except BaseException as e:  # noqa: BLE001
            _send({"type": "done", "answer": "", "error": f"{type(e).__name__}: {e}"[:300]})
        finally:
            signal.alarm(0)


if __name__ == "__main__":
    main()
