"""Small, conservative subprocess sandbox for generated Python functions.

The public :func:`evaluate` function is intentionally narrow.  ``source`` must
define exactly one function named ``evaluate``.  The function is checked with a
static AST allowlist before it is sent to a fresh Python interpreter.  Hidden
tests are JSON-like literals with this shape::

    {"args": [1, 2], "kwargs": {}, "expected": 3}

The sandbox is a containment boundary for the local experiment, not a claim of
perfect isolation against a hostile Python interpreter.  The allowlist keeps
the generated program pure and the subprocess adds wall-clock, CPU, memory,
file-size, and process-count limits where the host exposes them.
"""

from __future__ import annotations

import ast
import builtins
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from typing import Any


_MAX_SOURCE_BYTES = 100_000
_MAX_TEST_CASES = 256
_MAX_LITERAL_DEPTH = 8
_MAX_LITERAL_ITEMS = 256
_MAX_LITERAL_STRING_LENGTH = 8_192
_MAX_RESULT_MESSAGE_LENGTH = 1_000

_SAFE_BUILTIN_NAMES = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "float",
        "int",
        "len",
        "list",
        "max",
        "min",
        "range",
        "repr",
        "reversed",
        "round",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
    }
)

_SAFE_BINOP_TYPES = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)
_SAFE_UNARYOP_TYPES = (ast.UAdd, ast.USub, ast.Not, ast.Invert)
_SAFE_COMPARE_TYPES = (
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)


def _issue(code: str, message: str, node: ast.AST | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message}
    if node is not None and getattr(node, "lineno", None) is not None:
        item["line"] = node.lineno
        item["column"] = node.col_offset + 1
    return item


class _AstAllowlist(ast.NodeVisitor):
    """Reject everything outside a deliberately small pure-Python subset."""

    def __init__(self, function: ast.FunctionDef) -> None:
        self.function = function
        self.issues: list[dict[str, Any]] = []
        self.bound_names = self._collect_bound_names(function)

    @staticmethod
    def _collect_bound_names(function: ast.FunctionDef) -> set[str]:
        names = {
            argument.arg
            for argument in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            )
        }
        if function.args.vararg is not None:
            names.add(function.args.vararg.arg)
        if function.args.kwarg is not None:
            names.add(function.args.kwarg.arg)
        for node in ast.walk(function):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.add(node.id)
        return names

    def reject(self, code: str, message: str, node: ast.AST | None = None) -> None:
        self.issues.append(_issue(code, message, node))

    def validate(self) -> list[dict[str, Any]]:
        self.visit(self.function)
        return self.issues

    def generic_visit(self, node: ast.AST) -> None:
        self.reject(
            "disallowed_syntax",
            f"Syntax node {type(node).__name__} is not allowed in the sandbox.",
            node,
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is not self.function:
            self.reject("disallowed_syntax", "Nested function definitions are not allowed.", node)
            return
        if node.decorator_list:
            self.reject("disallowed_syntax", "Function decorators are not allowed.", node)
        if node.returns is not None or node.type_comment is not None:
            self.reject("disallowed_syntax", "Function annotations are not allowed.", node)
        self._visit_arguments(node.args)
        for statement in node.body:
            self.visit(statement)

    def _visit_arguments(self, node: ast.arguments) -> None:
        all_arguments = [*node.posonlyargs, *node.args, *node.kwonlyargs]
        if node.vararg is not None:
            all_arguments.append(node.vararg)
        if node.kwarg is not None:
            all_arguments.append(node.kwarg)
        for argument in all_arguments:
            if argument.annotation is not None:
                self.reject("disallowed_syntax", "Parameter annotations are not allowed.", argument)
            if argument.type_comment is not None:
                self.reject("disallowed_syntax", "Parameter type comments are not allowed.", argument)
        for default in [*node.defaults, *(item for item in node.kw_defaults if item is not None)]:
            self.visit(default)

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is not None:
            self.visit(node.value)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._visit_assignment_target(target)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.reject("disallowed_syntax", "Annotated assignments are not allowed.", node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if not isinstance(node.target, ast.Name):
            self.reject("disallowed_syntax", "Only local-name augmented assignments are allowed.", node)
        else:
            self.visit(node.target)
        self._visit_binop_operator(node.op, node)
        self.visit(node.value)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    def visit_For(self, node: ast.For) -> None:
        self._visit_assignment_target(node.target)
        self.visit(node.iter)
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    def visit_Break(self, node: ast.Break) -> None:
        return

    def visit_Continue(self, node: ast.Continue) -> None:
        return

    def visit_Expr(self, node: ast.Expr) -> None:
        self.visit(node.value)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in self.bound_names and node.id not in _SAFE_BUILTIN_NAMES:
            self.reject("disallowed_name", f"Name {node.id!r} is not allowed.", node)

    def visit_Constant(self, node: ast.Constant) -> None:
        value = node.value
        if isinstance(value, bool) or value is None or isinstance(value, (int, str)):
            if isinstance(value, str) and len(value) > _MAX_LITERAL_STRING_LENGTH:
                self.reject("literal_too_large", "String literals are too long.", node)
            return
        if isinstance(value, float) and math.isfinite(value):
            return
        self.reject("disallowed_literal", "Only finite JSON-like literals are allowed.", node)

    def visit_List(self, node: ast.List) -> None:
        self._check_literal_item_count(node.elts, node)
        for element in node.elts:
            self.visit(element)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self._check_literal_item_count(node.elts, node)
        for element in node.elts:
            self.visit(element)

    def visit_Dict(self, node: ast.Dict) -> None:
        self._check_literal_item_count(node.keys, node)
        for key, value in zip(node.keys, node.values):
            if key is None:
                self.reject("disallowed_syntax", "Dictionary unpacking is not allowed.", node)
            else:
                self.visit(key)
            self.visit(value)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Slice(self, node: ast.Slice) -> None:
        for value in (node.lower, node.upper, node.step):
            if value is not None:
                self.visit(value)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        self._visit_binop_operator(node.op, node)
        self.visit(node.left)
        self.visit(node.right)

    def _visit_binop_operator(self, operator: ast.operator, node: ast.AST) -> None:
        if not isinstance(operator, _SAFE_BINOP_TYPES):
            self.reject("disallowed_syntax", f"Operator {type(operator).__name__} is not allowed.", node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if not isinstance(node.op, _SAFE_UNARYOP_TYPES):
            self.reject("disallowed_syntax", f"Operator {type(node.op).__name__} is not allowed.", node)
        self.visit(node.operand)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        if not isinstance(node.op, (ast.And, ast.Or)):
            self.reject("disallowed_syntax", f"Operator {type(node.op).__name__} is not allowed.", node)
        for value in node.values:
            self.visit(value)

    def visit_Compare(self, node: ast.Compare) -> None:
        if any(not isinstance(operator, _SAFE_COMPARE_TYPES) for operator in node.ops):
            self.reject("disallowed_syntax", "This comparison operator is not allowed.", node)
        self.visit(node.left)
        for comparator in node.comparators:
            self.visit(comparator)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.visit(node.test)
        self.visit(node.body)
        self.visit(node.orelse)

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_BUILTIN_NAMES:
            self.reject("disallowed_call", "Only the small safe-builtin allowlist may be called.", node)
            if isinstance(node.func, ast.Name):
                self.visit(node.func)
        else:
            self.visit(node.func)
        for argument in node.args:
            if isinstance(argument, ast.Starred):
                self.reject("disallowed_syntax", "Starred call arguments are not allowed.", argument)
            else:
                self.visit(argument)
        for keyword in node.keywords:
            if keyword.arg is None:
                self.reject("disallowed_syntax", "Keyword unpacking is not allowed.", keyword)
            self.visit(keyword.value)

    def _visit_assignment_target(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            self.visit(node)
            return
        if isinstance(node, (ast.List, ast.Tuple)):
            for element in node.elts:
                self._visit_assignment_target(element)
            return
        self.reject("disallowed_syntax", "Only local-name assignment targets are allowed.", node)

    def _check_literal_item_count(self, items: Sequence[Any], node: ast.AST) -> None:
        if len(items) > _MAX_LITERAL_ITEMS:
            self.reject("literal_too_large", "Literal containers contain too many items.", node)


def _base_result() -> dict[str, Any]:
    return {
        "status": "rejected",
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "cases": [],
        "safety_controls": {},
        "safety_errors": [],
        "validation_errors": [],
        "timed_out": False,
        "duration_ms": 0.0,
    }


def _invalid_result(issues: list[dict[str, Any]]) -> dict[str, Any]:
    result = _base_result()
    result["validation_errors"] = issues
    return result


def _validate_literal(value: Any, *, path: str, depth: int, seen: set[int]) -> list[dict[str, Any]]:
    if depth > _MAX_LITERAL_DEPTH:
        return [_issue("invalid_test_literal", f"{path} is nested too deeply.")]
    if value is None or isinstance(value, (bool, int, str)):
        if isinstance(value, str) and len(value) > _MAX_LITERAL_STRING_LENGTH:
            return [_issue("invalid_test_literal", f"{path} contains an overly long string.")]
        return []
    if isinstance(value, float):
        return (
            []
            if math.isfinite(value)
            else [_issue("invalid_test_literal", f"{path} must contain a finite number.")]
        )
    if isinstance(value, (list, tuple)):
        identity = id(value)
        if identity in seen:
            return [_issue("invalid_test_literal", f"{path} contains a cycle.")]
        if len(value) > _MAX_LITERAL_ITEMS:
            return [_issue("invalid_test_literal", f"{path} contains too many items.")]
        seen.add(identity)
        issues: list[dict[str, Any]] = []
        for index, item in enumerate(value):
            issues.extend(_validate_literal(item, path=f"{path}[{index}]", depth=depth + 1, seen=seen))
        seen.remove(identity)
        return issues
    if isinstance(value, dict):
        identity = id(value)
        if identity in seen:
            return [_issue("invalid_test_literal", f"{path} contains a cycle.")]
        if len(value) > _MAX_LITERAL_ITEMS:
            return [_issue("invalid_test_literal", f"{path} contains too many items.")]
        seen.add(identity)
        issues = []
        for key, item in value.items():
            if not isinstance(key, str):
                issues.append(_issue("invalid_test_literal", f"{path} has a non-string dictionary key."))
            else:
                issues.extend(
                    _validate_literal(item, path=f"{path}[{key!r}]", depth=depth + 1, seen=seen)
                )
        seen.remove(identity)
        return issues
    return [_issue("invalid_test_literal", f"{path} contains {type(value).__name__}, which is not literal data.")]


def _validate_hidden_tests(hidden_tests: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    if not isinstance(hidden_tests, Sequence) or isinstance(hidden_tests, (str, bytes, bytearray)):
        return [_issue("invalid_test_literal", "hidden_tests must be a sequence of literal mappings.")], []
    if len(hidden_tests) > _MAX_TEST_CASES:
        issues.append(_issue("invalid_test_literal", "hidden_tests contains too many cases."))
    for index, case in enumerate(hidden_tests[:_MAX_TEST_CASES]):
        path = f"hidden_tests[{index}]"
        if not isinstance(case, Mapping):
            issues.append(_issue("invalid_test_literal", f"{path} must be a mapping."))
            continue
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        if not isinstance(args, list):
            issues.append(_issue("invalid_test_literal", f"{path}.args must be a list."))
            continue
        if not isinstance(kwargs, dict):
            issues.append(_issue("invalid_test_literal", f"{path}.kwargs must be a dictionary."))
            continue
        if "expected" not in case:
            issues.append(_issue("invalid_test_literal", f"{path}.expected is required."))
            continue
        for field, value in (("args", args), ("kwargs", kwargs), ("expected", case["expected"])):
            issues.extend(_validate_literal(value, path=f"{path}.{field}", depth=0, seen=set()))
        normalized.append({"args": args, "kwargs": kwargs, "expected": case["expected"]})
    return issues, normalized


def _validate_source(source: Any) -> list[dict[str, Any]]:
    if not isinstance(source, str):
        return [_issue("invalid_source", "source must be a string.")]
    if not source.strip():
        return [_issue("invalid_source", "source must not be empty.")]
    if len(source.encode("utf-8")) > _MAX_SOURCE_BYTES:
        return [_issue("invalid_source", "source is too large.")]
    try:
        tree = ast.parse(source, filename="<generated>", mode="exec")
    except SyntaxError as exc:
        item = _issue("syntax_error", exc.msg)
        if exc.lineno is not None:
            item["line"] = exc.lineno
        if exc.offset is not None:
            item["column"] = exc.offset
        return [item]
    except (MemoryError, RecursionError, ValueError) as exc:
        return [_issue("syntax_error", str(exc) or "source could not be parsed safely.")]
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        return [_issue("module_shape", "source must contain exactly one regular function definition.")]
    function = tree.body[0]
    if function.name != "evaluate":
        return [_issue("module_shape", "the only function must be named evaluate.", function)]
    return _AstAllowlist(function).validate()


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except (ProcessLookupError, PermissionError):
            pass
    process.kill()


_WORKER_SOURCE = r'''
import builtins
import json
import os
import sys
import time

try:
    import resource
except ImportError:
    resource = None


SAFE_NAMES = ''' + repr(sorted(_SAFE_BUILTIN_NAMES)) + r'''
MAX_OUTPUT_BYTES = 64 * 1024
REQUIRED_LIMITS = (
    ("cpu", "RLIMIT_CPU", 1),
    ("address_space", "RLIMIT_AS", 256 * 1024 * 1024),
    ("nproc", "RLIMIT_NPROC", 0),
    ("nofile", "RLIMIT_NOFILE", 64),
    ("output", "RLIMIT_FSIZE", MAX_OUTPUT_BYTES),
)


def shorten(value):
    return str(value)[:1000]


def apply_safety_controls():
    controls = {name: False for name, _attribute, _amount in REQUIRED_LIMITS}
    controls["non_root"] = True
    errors = []
    geteuid = getattr(os, "geteuid", None)
    if geteuid is not None:
        try:
            if geteuid() == 0:
                controls["non_root"] = False
                errors.append({"control": "non_root", "code": "root_user"})
        except OSError as exc:
            controls["non_root"] = False
            errors.append(
                {"control": "non_root", "code": "identity_check_failed", "message": str(exc)[:1000]}
            )

    if resource is None:
        errors.extend(
            {"control": name, "code": "resource_module_unavailable"}
            for name, _attribute, _amount in REQUIRED_LIMITS
        )
        return controls, errors

    for name, attribute, requested in REQUIRED_LIMITS:
        kind = getattr(resource, attribute, None)
        if kind is None:
            errors.append({"control": name, "code": "limit_unavailable"})
            continue
        try:
            _soft, hard = resource.getrlimit(kind)
            if hard == resource.RLIM_INFINITY:
                target = requested
            else:
                target = min(requested, hard)
            if target < 0 or (name != "nproc" and target == 0):
                raise ValueError("host hard limit does not permit a positive sandbox limit")
            resource.setrlimit(kind, (target, target))
            controls[name] = True
        except (OSError, ValueError, AttributeError) as exc:
            errors.append(
                {"control": name, "code": "limit_apply_failed", "message": str(exc)[:1000]}
            )
    return controls, errors


def emit(result):
    encoded = json.dumps(result, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_OUTPUT_BYTES:
        encoded = json.dumps(
            {
                "status": "output_limit_exceeded",
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "cases": [],
                "validation_errors": [],
                "timed_out": False,
                "safety_controls": result.get("safety_controls", {}),
                "safety_errors": [
                    {"control": "output", "code": "output_limit_exceeded"}
                ],
            },
            separators=(",", ":"),
        ).encode("utf-8")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    payload = json.load(sys.stdin)
    start = time.monotonic()
    result = {
        "status": "worker_error",
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "cases": [],
        "safety_controls": {},
        "safety_errors": [],
        "validation_errors": [],
        "timed_out": False,
    }
    controls, safety_errors = apply_safety_controls()
    result["safety_controls"] = controls
    result["safety_errors"] = safety_errors
    if safety_errors or not all(controls.values()):
        result["status"] = "unsafe_not_run"
        emit(result)
        return
    try:
        namespace = {"__builtins__": {name: getattr(builtins, name) for name in SAFE_NAMES}}
        code = compile(payload["source"], "<generated>", "exec", dont_inherit=True)
        exec(code, namespace, namespace)
        function = namespace["evaluate"]
        if not callable(function):
            raise TypeError("evaluate is not callable")
    except BaseException as exc:
        result["status"] = "runtime_error"
        result["errors"] = 1
        result["worker_error"] = {"exception_type": type(exc).__name__, "message": shorten(exc)}
        result["duration_ms"] = round((time.monotonic() - start) * 1000, 3)
        emit(result)
        return

    for index, case in enumerate(payload["tests"]):
        try:
            actual = function(*case["args"], **case["kwargs"])
            json.dumps(actual, allow_nan=False)
        except BaseException as exc:
            result["errors"] += 1
            result["cases"].append(
                {
                    "index": index,
                    "status": "runtime_error",
                    "exception_type": type(exc).__name__,
                    "message": shorten(exc),
                }
            )
            continue
        if actual == case["expected"]:
            result["passed"] += 1
            result["cases"].append({"index": index, "status": "passed"})
        else:
            result["failed"] += 1
            result["cases"].append(
                {
                    "index": index,
                    "status": "failed",
                    "expected": case["expected"],
                    "actual": actual,
                }
            )
    if result["errors"]:
        result["status"] = "runtime_error"
    elif result["failed"]:
        result["status"] = "failed"
    else:
        result["status"] = "passed"
    result["duration_ms"] = round((time.monotonic() - start) * 1000, 3)
    emit(result)


if __name__ == "__main__":
    main()
'''


def evaluate(
    source: str,
    hidden_tests: Sequence[Mapping[str, Any]],
    *,
    timeout_seconds: float = 1.0,
) -> dict[str, Any]:
    """Validate and execute one generated ``evaluate`` function.

    The return value is always a JSON-serializable dictionary.  No subprocess
    is started when source or hidden tests fail validation.
    """

    source_issues = _validate_source(source)
    test_issues, normalized_tests = _validate_hidden_tests(hidden_tests)
    issues = [*source_issues, *test_issues]
    if issues:
        return _invalid_result(issues)
    if not isinstance(timeout_seconds, (int, float)) or isinstance(timeout_seconds, bool):
        return _invalid_result([_issue("invalid_timeout", "timeout_seconds must be a positive number.")])
    if not math.isfinite(float(timeout_seconds)) or timeout_seconds <= 0 or timeout_seconds > 60:
        return _invalid_result([_issue("invalid_timeout", "timeout_seconds must be in (0, 60].")])

    try:
        payload = json.dumps(
            {"source": source, "tests": normalized_tests},
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        return _invalid_result([_issue("invalid_test_literal", str(exc))])

    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="codegen-sandbox-") as working_directory:
            process = subprocess.Popen(
                [sys.executable, "-I", "-c", _WORKER_SOURCE],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                cwd=working_directory,
                env={},
                start_new_session=os.name == "posix",
            )
            try:
                stdout, stderr = process.communicate(payload, timeout=float(timeout_seconds))
            except subprocess.TimeoutExpired:
                _terminate_process(process)
                process.communicate()
                result = _base_result()
                result["status"] = "timeout"
                result["timed_out"] = True
                result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
                return result
    except (OSError, RuntimeError) as exc:
        result = _base_result()
        result["status"] = "unsafe_not_run"
        result["safety_errors"] = [
            {"control": "child_setup", "code": "isolation_setup_failed", "message": str(exc)[:_MAX_RESULT_MESSAGE_LENGTH]}
        ]
        result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
        return result

    duration_ms = round((time.monotonic() - started) * 1000, 3)
    if process.returncode != 0:
        result = _base_result()
        result["status"] = "worker_error"
        result["duration_ms"] = duration_ms
        result["worker_error"] = {
            "return_code": process.returncode,
            "stderr": stderr.decode("utf-8", errors="replace")[:_MAX_RESULT_MESSAGE_LENGTH],
        }
        return result
    try:
        result = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        result = _base_result()
        result["status"] = "worker_error"
        result["duration_ms"] = duration_ms
        result["worker_error"] = {"message": str(exc)}
        return result
    if not isinstance(result, dict):
        invalid = _base_result()
        invalid["status"] = "worker_error"
        invalid["duration_ms"] = duration_ms
        invalid["worker_error"] = {"message": "worker returned a non-object result"}
        return invalid
    result["duration_ms"] = duration_ms
    result.setdefault("timed_out", False)
    result.setdefault("validation_errors", [])
    return result


def _trusted_fixture_builtins() -> dict[str, Any]:
    return {name: getattr(builtins, name) for name in _SAFE_BUILTIN_NAMES}


def evaluate_trusted_fixture(
    source: str,
    hidden_tests: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate a checked-in reference implementation without claiming isolation.

    This escape hatch is only for the offline discovery stub after the caller
    has verified that ``source`` is byte-for-byte one of the checked-in
    reference implementations.  Provider output must always use :func:`evaluate`.
    """

    source_issues = _validate_source(source)
    test_issues, normalized_tests = _validate_hidden_tests(hidden_tests)
    if source_issues or test_issues:
        return _invalid_result([*source_issues, *test_issues])
    started = time.monotonic()
    result = _base_result()
    result["execution_mode"] = "trusted_fixture"
    try:
        namespace = {"__builtins__": _trusted_fixture_builtins()}
        exec(compile(source, "<trusted-reference>", "exec", dont_inherit=True), namespace, namespace)
        function = namespace["evaluate"]
        for index, case in enumerate(normalized_tests):
            try:
                actual = function(*case["args"], **case["kwargs"])
                json.dumps(actual, allow_nan=False)
            except BaseException as exc:
                result["errors"] += 1
                result["cases"].append(
                    {
                        "index": index,
                        "status": "runtime_error",
                        "exception_type": type(exc).__name__,
                        "message": str(exc)[:_MAX_RESULT_MESSAGE_LENGTH],
                    }
                )
                continue
            if actual == case["expected"]:
                result["passed"] += 1
                result["cases"].append({"index": index, "status": "passed"})
            else:
                result["failed"] += 1
                result["cases"].append(
                    {
                        "index": index,
                        "status": "failed",
                        "expected": case["expected"],
                        "actual": actual,
                    }
                )
        if result["errors"]:
            result["status"] = "runtime_error"
        elif result["failed"]:
            result["status"] = "failed"
        else:
            result["status"] = "passed"
    except BaseException as exc:
        result["status"] = "runtime_error"
        result["errors"] = 1
        result["worker_error"] = {
            "exception_type": type(exc).__name__,
            "message": str(exc)[:_MAX_RESULT_MESSAGE_LENGTH],
        }
    result["duration_ms"] = round((time.monotonic() - started) * 1000, 3)
    result["safety_controls"] = {"trusted_reference_match": True, "subprocess_isolation": False}
    result["safety_errors"] = [
        {"control": "subprocess_isolation", "code": "trusted_fixture_only"}
    ]
    return result


__all__ = ["evaluate", "evaluate_trusted_fixture"]
