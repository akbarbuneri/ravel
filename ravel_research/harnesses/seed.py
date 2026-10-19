import re


def run(question, tools):
    # Portfolio requests: enforce entitlements before reading account data.
    m = re.search(r"\bA-\d+\b", question)
    if m:
        account = m.group(0)
        if not tools.is_authorized(account):
            return "UNAUTHORIZED"
        return str(tools.get_portfolio(account)["total_value"])

    # Everything else: retrieve documents and ask the solver once.
    docs = tools.search(question, k=4)
    context = "\n".join("- " + d["text"] for d in docs)
    prompt = (
        "Use the documents to answer the question.\n"
        f"Documents:\n{context}\n\n"
        f"Question: {question}\n"
        "Reply with only the final number (no units, no words)."
    )
    return tools.llm(prompt, max_tokens=24).strip()
