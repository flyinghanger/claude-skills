# My Claude Code Skills

Personal skill collection for Claude Code / OpenClaw.

## Skills

| Skill | Description | Install |
|-------|-------------|---------|
| [content-pipeline](./content-pipeline/) | Content production pipeline with 10-dimension scoring, fact-check, and evolving standards | `flyinghanger/my-skills@content-pipeline` |

## Install

```bash
# In Claude Code
/install-skill flyinghanger/my-skills@content-pipeline
```


## Usage

```bash
/content-pipeline article.md draft        # Write first draft
/content-pipeline article.md fact-check   # Verify all claims
/content-pipeline article.md score        # 10-dimension scoring
/content-pipeline article.md full         # Run full pipeline
/content-pipeline article.md evolve       # Post-publish feedback loop
```

## License

MIT
