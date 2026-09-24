"""Regression tests for #641, without starting NoneBot or contacting QQ.

Load the production definitions via AST to avoid plugin import-time startup and
optional integrations. Only external I/O is mocked; batching and handlers execute
their actual source code.
"""

import ast
import re
import unittest
from inspect import signature
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple
from unittest.mock import Mock


ROOT = Path(__file__).resolve().parents[1] / "src/plugins/ELF_RSS2"


def load_definitions(path, names, namespace):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tree.body = [node for node in tree.body if getattr(node, "name", None) in names]
    exec(compile(tree, str(path), "exec"), namespace)


class BatchFinalizationTests(unittest.IsolatedAsyncioTestCase):
    async def check_run(self, count, forward, failures, duplicate_filter):
        db = Mock()
        conn = Mock() if duplicate_filter else None
        logger = Mock()
        cache_manage = Mock()
        sent = []
        batch_sizes = []
        entries = [{"title": str(i)} for i in range(count)]
        rss = SimpleNamespace(
            name="test", send_forward_msg=forward, get_url=lambda: "https://example.com"
        )

        async def send(rss, messages, items, state):
            db.close.assert_not_called()
            if conn is not None:
                conn.close.assert_not_called()
            self.assertEqual(len(messages), len(items))
            sent.extend(items)
            state["error_count"] += sum(int(item["title"]) < failures for item in items)

        ns = dict(globals(), Rss=SimpleNamespace(handle_name=lambda name: name),
                  DATA_PATH=Path("unused"), TinyDB=Mock(return_value=db),
                  logger=logger, cache_json_manage=cache_manage, handle_send_msgs=send)
        load_definitions(ROOT / "utils.py", {"partition_list"}, ns)
        load_definitions(ROOT / "parsing/parsing_rss.py", {
            "ParsingItem", "ParsingBase", "_sort", "_handler_filter", "_run_handlers", "ParsingRss"
        }, ns)
        load_definitions(ROOT / "parsing/__init__.py", {"handle_message", "after_handler"}, ns)

        @ns["ParsingBase"].append_before_handler()
        async def before():
            return {"change_data": entries.copy(), "conn": conn}

        @ns["ParsingBase"].append_after_handler(priority=1)
        async def observe(state):
            db.close.assert_not_called()
            logger.info.assert_not_called()
            logger.error.assert_not_called()
            batch_sizes.append(len(state["items"]))
            return {}

        parser = ns["ParsingRss"](rss)
        await parser.start("test", {"feed": {"title": "test"}, "entries": entries})

        self.assertEqual(sent, entries)
        self.assertEqual(batch_sizes, [min(10, count - i) for i in range(0, count, 10)] or [0])
        db.close.assert_called_once_with()
        if conn is not None:
            conn.close.assert_called_once_with()
        self.assertEqual(cache_manage.call_count, len(batch_sizes))
        cache_manage.assert_called_with(db, count)
        if count == 0:
            logger.info.assert_called_once_with("test 没有新信息")
        elif failures == count:
            logger.error.assert_called_once_with(f"test 新消息推送失败，共计：{count}")
        else:
            logger.info.assert_called_once_with(f"test 新消息推送完毕，共计：{count - failures}/{count}")
        self.assertEqual(logger.info.call_count + logger.error.call_count, 1)

    async def test_batch_boundaries(self):
        for count in (0, 1, 5, 10, 11, 15, 20, 21, 25, 30, 40):
            for forward in (False, True):
                for duplicate_filter in (False, True):
                    with self.subTest(count=count, forward=forward, duplicate_filter=duplicate_filter):
                        await self.check_run(count, forward, 0, duplicate_filter)

    async def test_failed_sends_still_finalize(self):
        for forward in (False, True):
            for failures in (3, 20):
                with self.subTest(forward=forward, failures=failures):
                    await self.check_run(20, forward, failures, True)


if __name__ == "__main__":
    unittest.main()
