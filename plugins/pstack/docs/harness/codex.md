# pstack in Codex

superkit adds this file to its copy of pstack. It is not part of pstack upstream.

pstack skills use Cursor names. In Codex, read this file once per session, then map each Cursor name in a skill with the tables below. `<pstack>` means the folder that holds `skills/` and `docs/`, two levels above any pstack `SKILL.md`. Codex hides most pstack skills from its skill list, but it lists `pstack:setup-pstack` with its path, so take `<pstack>` from that entry. If a Cursor field has no row, drop it and say so. Never pass a field or value the tool schema rejects.

The tool names below are the ones Codex 0.160.0 offered. Use them when your session offers them. If it offers a different tool for the same job, use that tool. If it offers none, follow the fallback in the row.

## Tools

| Cursor | Codex |
| --- | --- |
| `Task` | `spawn_agent`. Collect each result with `wait_agent`, and prefer long waits. If the session has no subagent tool, do the step yourself and say so. Never report your own pass as an independent agent's result. |
| `AskQuestion` | `request_user_input` when the turn lists it. Codex lists it only in some modes. Otherwise ask in plain text. |
| Open a todolist, or copy steps into the todolist tool | Use the session's plan tool if it offers one. Otherwise keep the list in your reply and update it at each phase. |
| Run another pstack skill (`/name` or "the **name** skill") | Read `<pstack>/skills/<name>/SKILL.md` and follow it. Codex hides most pstack skills from its skill list, because their `agents/openai.yaml` turns off implicit invocation, as `disable-model-invocation` does in Cursor. A missing entry does not mean pstack is absent. Codex names pstack skills `pstack:<name>` and runs a skill that the user mentions with `$`. When you tell the user to type one, write `$pstack:<name>`. |
| `Grep`, `Glob` | The shell with `rg`. |

## Subagent fields

| Cursor | Codex |
| --- | --- |
| `subagent_type: generalPurpose` | `spawn_agent` with no role document. |
| `poteto-agent`, `comment-sicko` | Codex does not register `<pstack>/agents/` as agent types, so never pass these names as a type. Spawn a subagent and start its brief with the absolute path of `<pstack>/agents/<name>.md` as its role document. It reads that file first and follows it. For `poteto-agent`, also give the absolute paths of `<pstack>/skills/poteto-mode/SKILL.md` and of this file. |
| The `model:` line in `poteto-agent`'s file | It holds a Cursor slug, so it never reaches Codex. Set `model` and `reasoning_effort` with the Models table. |
| The brief of a `Task` | Pass `fork_turns: "none"`, so the agent sees only the brief, as a Cursor `Task` does. Pass more turns only when the skill asks the worker to see the conversation. A full-history fork also ignores `model` and `reasoning_effort`. |
| `readonly: true` | Codex has no read-only agent type. The brief says "do not edit files, and do not change the index, branches, or config", and you check `git status` afterward. This is an instruction, not a sandbox. |
| `readonly: false` | A default subagent. |
| `environment: "cloud"` | All Codex agents share your working directory, so each edit is visible to every agent at once. Before the spawn, run `git worktree add <path> <branch-or-commit>` and tell the worker to work only in `<path>`. If you cannot make a worktree, run workers that edit the same files one after another, and say so. |
| `environment: "local"` | Omit. |
| `cloud_base_branch: <b>` | Make the worktree from `<b>`. |
| `run_in_background: true` | Omit. A spawned agent runs while you keep working. Call `wait_agent` when you need its result. |
| `resume` | `followup_task` gives an agent you spawned in this session a new task. Otherwise spawn a new agent and paste the earlier result into its brief. |
| `file_attachments` | List the absolute paths in the brief. |
| Many parallel spawns, as in arena, swarm, interrogate, and autopilot | Codex 0.160.0 had 4 concurrent agent slots, and you use one of them. Run a larger fan-out in batches that fit the free slots, and say so. |

## Models

| Cursor | Codex |
| --- | --- |
| `claude-<family>-<version>-<effort>[-fast]`, such as `claude-opus-5-5-xhigh` | Codex runs only the models in its own catalog. Omit `model` so the agent runs on the session model, and say so. Pass the effort as `reasoning_effort`, such as `xhigh`. Drop `-fast`. |
| A `gemini-*` or other non-Claude slug | Pass it as `model` only when Codex's catalog has it. Otherwise omit `model`, as above. Pass its effort as `reasoning_effort`. |
| A panel or pool of several models, such as `arena runners`, `arena cross-judge pool`, or `interrogate reviewers` | Run one agent per entry, as the skill says. If two entries map to the same Codex model, say that the panel lost that model diversity. The arena judge must come from a vendor other than the parent's. If no entry qualifies, skip the judge and say so, as the arena skill allows. |
| `auto` or `inherit-parent` | Omit `model` and `reasoning_effort`. |
| The `pstack-models.mdc` rule, `~/.cursor/rules/pstack-models.mdc` | `$CODEX_HOME/pstack-models.md`, which is `~/.codex/pstack-models.md` when `CODEX_HOME` is unset. Codex does not load it on its own. Read it right after this file, once per session. If the file or the role's line is missing, use the skill's default slug, mapped with the rows above. |
| A role value `<model> <effort>`, such as `opus high` | `model` and `reasoning_effort`, such as `gpt-5.5 xhigh`. |

## setup-pstack

Codex does not load a rules folder into each session, so `setup-pstack` writes a file that this adapter reads. Follow its steps with these changes:

- Detect. The detected models are the `model` values that the `spawn_agent` schema lists, each with an effort from its `reasoning_effort` values. If the schema lists none, `codex debug models` prints Codex's model catalog with each model's reasoning levels. Write a real model as `<model> <effort>`, such as `gpt-5.5 xhigh`. The effort is the last token, so the budget step works as written.
- Defaults. Every default slug names a Claude or Gemini model, and Codex runs neither. Map each default to `inherit-parent`. A panel default keeps its length, so three `inherit-parent` entries still run three agents. The budget does not change `inherit-parent`, so it applies only to roles the user sets to a Codex model. Say so when you ask for the budget.
- Write. Write `$CODEX_HOME/pstack-models.md` with no frontmatter, then the comment lines, the `# budget` line, and one line per role from step 5. Overwrite the whole file. Never put the role lines in `AGENTS.md`. If the sandbox refuses the write, ask for approval, or show the file and its path so the user can save it.
- Confirm. Say that the file applies from the next pstack skill run, because every pstack skill reads it through this adapter.

## Paths

| Cursor | Codex |
| --- | --- |
| `.cursor/skills/`, `~/.cursor/skills/` | `.agents/skills/`, `~/.agents/skills/` |
| Install steps: `/add-plugin pstack`, or `pstack@cursor-plugins` in Claude Code | In Codex, this copy installs from the superkit marketplace: `codex plugin marketplace add Cho-D-YoungRae/superkit`, then `codex plugin add pstack@superkit`. |
| `~/.cursor/plugins/`, `.cursor-plugin/plugin.json` | `$CODEX_HOME/plugins/cache/<marketplace>/<plugin>/<version>/`, `.claude-plugin/plugin.json`. Codex reads that manifest for this package. |
| `.cursor/rules/*.mdc`, always-applied rules | `AGENTS.md`. Codex never reads `.mdc` files, and it does not read `CLAUDE.md` on its own. The model rule is the exception. See Models. |
| `https://github.com/cursor/plugins/blob/main/pstack/<path>` | `<pstack>/<path>` when that file exists. The plugin ships the skills, `docs/guide/`, and `README.md`. Read the local copy and never fetch it. Give the user the URL when they need a link. |
| Transcripts in `~/.cursor/projects/<slug>/agent-transcripts/` | `$CODEX_HOME/sessions/<yyyy>/<mm>/<dd>/rollout-*.jsonl`, one file per session. The first line has `"type": "session_meta"`, and its `payload.cwd` is the session's working directory. Read only files whose `cwd` is this workspace. The newest one is usually the current session, but agents you spawned can write their own files with the same `cwd`. |

## Cursor-only features

Codex has no Cursor Automations, Bugbot, Cursor cloud agents, or Cursor's built-in PR tool. When a step needs one, put one line in your reply, `Skipped in Codex: <step>. <reason>.`, then go on to the next step. Do not stop, ask, or retry. When a later step needs what the skipped step made, such as a URL or a key, leave a placeholder and name it in the line.

| Cursor | Codex |
| --- | --- |
| Cursor Automations: routines, `update_state` routine calls, `api2.cursor.sh/automations` webhooks, routine wakes, and `SendToUser` secret requests | Skip with the line. |
| Bugbot | Bugbot comments on a GitHub PR are ordinary review threads, so triage them with the forge command that the step gives. Skip a step that starts, waits for, or configures Bugbot when the PR has no Bugbot check or comment. |
| Cursor cloud agents | `environment: "cloud"` maps to a worktree, as in Subagent fields. Skip a step that needs the cloud agent itself, such as its dashboard status or its own machine. |
| A built-in PR tool | Use the forge command that the step gives, such as `gh pr create`. That is not a skip, so write no line. |
| `/loop`, custom modes, `/autopilot` | Cursor built-ins with no Codex command. Skip with the line. |
| `/create-skill` | Codex's `skill-creator` skill when the skill list shows it. Otherwise skip with the line. |
| `/deslop`, `control-ui`, `control-cli` | These ship in Cursor's `cursor-team-kit` plugin, not in pstack. Use them when the session lists them. Otherwise skip with the line. |
