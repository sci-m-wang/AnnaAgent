# Publishing AnnaAgent Skills Publicly

This reference is for publishing `skills/annaagent-seeker-simulation/` to a
public registry such as ClawHub or any platform that indexes file-based agent
skills.

## Registry-Ready Requirements

- Keep `SKILL.md` at the root of the skill folder.
- Keep YAML frontmatter with `name` and `description`.
- Keep references under `references/` and use relative links from `SKILL.md`.
- Avoid secrets, local paths, API keys, generated logs, and private endpoints.
- Include paper and repository links for attribution.
- Tag a repository release so registries can pin immutable skill versions.

## Public URLs

After merging to `main`, the skill is publicly accessible at these stable paths:

```text
https://github.com/sci-m-wang/AnnaAgent/tree/main/skills/annaagent-seeker-simulation
https://raw.githubusercontent.com/sci-m-wang/AnnaAgent/main/skills/annaagent-seeker-simulation/SKILL.md
```

For versioned registry submissions, prefer a tag URL, for example:

```text
https://github.com/sci-m-wang/AnnaAgent/tree/v0.3.0/skills/annaagent-seeker-simulation
```

## ClawHub-Style Submission Checklist

If the registry supports GitHub import:

1. Submit repository: `https://github.com/sci-m-wang/AnnaAgent`.
2. Skill path: `skills/annaagent-seeker-simulation`.
3. Version/tag: use the latest release tag, such as `v0.3.0`.
4. Category: healthcare simulation, research tools, CLI automation, or agent
   operations depending on the registry taxonomy.
5. Description: reuse the `description` field from `SKILL.md`.
6. Visibility: public.

If the registry requires an archive, zip the skill folder only:

```bash
cd skills
zip -r annaagent-seeker-simulation.skill.zip annaagent-seeker-simulation
```

Do not include `.env`, `.venv`, run outputs, local memory DBs, or docs build
artifacts in the archive.

## Maintenance

- Update the skill when CLI semantics change.
- Keep the skill aligned with the latest PyPI version.
- Add a changelog note when a release changes initialization semantics.
- Re-run basic smoke checks before submitting to a public registry.
