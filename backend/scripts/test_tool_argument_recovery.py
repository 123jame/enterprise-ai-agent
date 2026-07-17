from app.llm.client import LLMClient


def main() -> None:
    broken = '{"path": "docs/PRD.md", "content": "# PRD\\n\\nHello **world**'
    args = LLMClient._parse_arguments("write_file", broken)

    assert args.get("path") == "docs/PRD.md"
    assert "PRD" in args.get("content", "")

    print("tool argument recovery: PASS")


if __name__ == "__main__":
    main()
