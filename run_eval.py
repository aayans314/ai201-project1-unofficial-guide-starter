"""Evaluation runner: run the 5 test questions from planning.md (plus one
out-of-scope probe) through the full RAG pipeline and dump everything needed
for the evaluation report to eval_results.md.

Accuracy judgments are made by a human (me) against the expected answers —
this script just collects the evidence.

Run: python run_eval.py
"""

from pathlib import Path

from query import ask

QUESTIONS = [
    {
        "q": "What is Doghead and when does it happen?",
        "expected": "Colby's biggest tradition: a St. Patrick's Day-style celebration on the "
                    "weekend before spring break where people stay up all night, and whoever "
                    "makes it through watches the sunrise (from the library steps).",
    },
    {
        "q": "Can freshmen choose their dorm at Colby?",
        "expected": "No. The only real preference is requesting substance-free housing; freshmen "
                    "fill out a questionnaire (sleep hours, tidiness, sociability) used for "
                    "roommate matching and are placed in designated freshman buildings.",
    },
    {
        "q": "Do Colby dorms have air conditioning?",
        "expected": "No — only the Johnson Pond houses have AC. Students say to bring a fan; "
                    "you only really want AC for about two weeks of the year. Heaters yes.",
    },
    {
        "q": "Which dining halls do students recommend for lunch vs dinner?",
        "expected": "One student's favorite combo: lunch at Foss, dinner at Bob's. Students also "
                    "recommend checking menus because halls vary day to day (Dana's station has "
                    "about a 70% hit rate).",
    },
    {
        "q": "How many on-campus Jan Plans are students expected to complete?",
        "expected": "Three on-campus JanPlans, and freshman year is expected to be one of them. "
                    "Personal alternatives can be proposed but take effort.",
    },
    {
        "q": "How much does tuition cost at Colby?",
        "expected": "(out-of-scope probe) The system should refuse — tuition figures are not in "
                    "the documents.",
    },
]


def main():
    lines = ["# Evaluation run results", ""]
    for i, item in enumerate(QUESTIONS, 1):
        print(f"Running Q{i}: {item['q']}")
        result = ask(item["q"])
        lines += [
            f"## Q{i}: {item['q']}",
            "",
            f"**Expected:** {item['expected']}",
            "",
            f"**System response:**",
            "",
            result["answer"],
            "",
            "**Sources returned:**",
            "",
        ]
        lines += [f"- {s}" for s in result["sources"]] or ["- (none)"]
        lines += ["", "**Retrieved chunks:**", ""]
        for j, h in enumerate(result["hits"], 1):
            lines.append(f"{j}. `d={h['distance']}` `{h['source_doc']}` — {h['text']}")
        lines += ["", "---", ""]

    Path("eval_results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\nWrote eval_results.md")


if __name__ == "__main__":
    main()
