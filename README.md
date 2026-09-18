# TypeSafe Agent Skills (fork)

Fork of [typesafe-ai/skills](https://github.com/typesafe-ai/skills), MIT licensed.
Upstream's `typesafe-ai` skill is kept unchanged. This fork adds one skill:

| Skill | What it adds |
|---|---|
| `typesafe-decisions` | The question-design rules stated as steps, worked templates for routing, reranking, passage gating, entity alignment, citation checking and multi-label tagging, a request validator that runs offline, an evaluation playbook, and measured results from two head-to-head evaluations against gpt-5.6-luna and gpt-oss-20b. Runs in Claude Code and Codex from one source directory. |

Install it into both hosts:

```bash
skills/typesafe-decisions/scripts/install.sh          # symlinks into ~/.claude/skills and ~/.codex/skills
skills/typesafe-decisions/scripts/install.sh --copy   # copies instead
```

Check a request before sending it:

```bash
python3 skills/typesafe-decisions/scripts/validate_request.py request.json
```

Sync upstream with `git fetch upstream && git merge upstream/main`.

---


Agent skills for building with [TypeSafe](https://typesafe.ai): typed decisions and probabilities from System One models.

You can [read SKILL.md on GitHub](https://github.com/typesafe-ai/skills/blob/main/skills/typesafe-ai/SKILL.md) or fetch its [raw Markdown](https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md).

## Install

### Claude Code plugin

Run in your terminal:

```bash
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai
```

### Other agents via skills.sh

```bash
npx skills add typesafe-ai/skills --skill typesafe-ai
```

Select your agent when prompted. Installation is project-local by default; add `-g` to install globally.

See the [installation guide](https://docs.typesafe.ai/agent-skill#installation) for a prompt to copy to your agent, manual installation, and updates.

## Use

Ask your agent, for example:

> Use TypeSafe to route incoming support tickets by department, with human review for uncertain decisions.

In Claude Code, you can explicitly invoke the plugin skill with `/typesafe:typesafe-ai`.

| Skill | Purpose |
|---|---|
| [typesafe-ai](skills/typesafe-ai/SKILL.md) | Design TypeSafe workflows, find current docs and cookbooks, and compose typed judgments in code |

## License

[MIT](LICENSE).
