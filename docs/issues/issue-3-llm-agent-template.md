# [Good First Issue] feat(templates): Add llm-agent boilerplate template

**Labels**: `good first issue`, `templates`, `sdk`  
**Target Directory**: `src/formicx/templates/llm-agent/`

## Description
Create a pre-packaged `llm-agent` template demonstrating how a Formicx agent can interact with LLM providers inside the `on_message` callback.

## Acceptance Criteria
- [ ] Create `agent.yaml.template` and `agent.py.template` inside `src/formicx/templates/llm-agent/`.
- [ ] Support `formicx agent create my-llm --template llm-agent`.
- [ ] Validate that `formicx agent validate` works on the generated scaffold.
