# Documentation Update Process

This document defines the process for maintaining the hybrid documentation framework to ensure it stays current and valuable.

## Documentation Architecture

Our hybrid documentation system consists of three layers:

1. **Auto-Generated Reference** (Low maintenance) - Generated from tool schemas
2. **Conceptual Documentation** (Stable content) - Manual, focuses on patterns and mental models  
3. **Living Examples** (Self-maintaining) - Executable code that serves as both docs and tests

## Maintenance Responsibilities

### Auto-Generated Documentation (scripts/generate_docs.py)

**When to Update:** Automatically when tool schemas change

**Process:**
1. Run `python scripts/generate_docs.py` after any tool changes
2. Review generated files for completeness
3. Commit updated reference documentation

**Files Affected:**
- `docs/tools/reference/*.md` (regenerated)
- `docs/tools/schemas/*.json` (regenerated)
- `docs/tools/README.md` (tool list updated)

### Conceptual Documentation (docs/tools/concepts/)

**When to Update:** Only when fundamental tool concepts change

**Triggers for Updates:**
- New tool categories added
- Major changes to tool mental models
- Security model changes
- Integration pattern changes

**Review Process:**
1. Assess if change affects tool concepts or just implementation
2. If conceptual impact, update relevant concept documents
3. Focus on patterns and mental models, not specific parameters
4. Maintain stability - avoid frequent updates

**Files to Consider:**
- `file-operations.md` - READ/WRITE/UPDATE concepts
- `search-and-discovery.md` - FIND tool concepts
- `task-management.md` - TODO/TASK concepts
- `security-model.md` - Security framework concepts

### Living Examples (docs/tools/examples/)

**When to Update:** When examples break or new patterns emerge

**Validation Process:**
1. Run examples before major releases
2. Fix broken examples immediately
3. Add new examples for common patterns
4. Keep examples focused and self-contained

**Example Categories:**
- `workflows/` - End-to-end scenario demonstrations
- `tool_demos/` - Individual tool usage patterns
- `integration_patterns/` - Common tool combinations

## Update Workflow

### For Tool Schema Changes (Common)

```bash
# 1. Make tool changes
# 2. Regenerate documentation
python scripts/generate_docs.py

# 3. Review changes
git diff docs/tools/reference/
git diff docs/tools/schemas/

# 4. Commit if satisfied
git add docs/tools/reference/ docs/tools/schemas/
git commit -m "Update tool documentation for schema changes"
```

### For New Tools (Uncommon)

```bash
# 1. Implement new tool
# 2. Add to documentation generator
# Edit scripts/generate_docs.py to include new tool

# 3. Regenerate all documentation
python scripts/generate_docs.py

# 4. Consider if new conceptual documentation needed
# Create new concept document if tool introduces new category

# 5. Add integration examples
# Create examples showing how new tool works with existing ones
```

### For Conceptual Changes (Rare)

```bash
# 1. Identify conceptual impact
# 2. Update relevant concept documents
# Edit docs/tools/concepts/*.md

# 3. Update integration examples if needed
# 4. Review cross-references and navigation
```

## Quality Assurance

### Documentation Completeness Checklist

- [ ] All tools have auto-generated reference documentation
- [ ] All tools are included in main README
- [ ] All tool categories have conceptual documentation
- [ ] Examples cover common usage patterns
- [ ] Cross-references are current and working
- [ ] Security considerations are documented

### Content Quality Standards

**Reference Documentation (Auto-Generated):**
- Complete parameter coverage
- Accurate type information
- Valid example syntax
- Security notes included

**Conceptual Documentation (Manual):**
- Focuses on stable concepts, not implementation details
- Includes mental models and when-to-use guidance
- Covers integration patterns
- Provides troubleshooting guidance

**Living Examples (Executable):**
- Actually executable (when version control established)
- Demonstrate real-world patterns
- Include error handling
- Cover edge cases

## Automation Opportunities

### Current Automation
- Parameter schemas auto-extracted from tool code
- Reference documentation auto-generated
- Example structure and navigation

### Future Automation Possibilities
- Automated testing of living examples
- Link checking for cross-references
- Documentation coverage analysis
- Automatic detection of missing documentation

## Review Process

### For Major Tool Changes
1. **Impact Assessment**: Determine documentation layers affected
2. **Auto-Generation**: Run documentation generator
3. **Concept Review**: Assess if conceptual docs need updates
4. **Example Validation**: Ensure examples still work
5. **Cross-Reference Check**: Verify links and navigation

### For Documentation-Only Changes
1. **Clarity Review**: Ensure content is clear and helpful
2. **Accuracy Check**: Verify information is current
3. **Consistency Review**: Check formatting and style
4. **Navigation Test**: Ensure users can find information

## Common Maintenance Tasks

### Weekly
- Review any broken links or references
- Check for new GitHub issues related to documentation

### Monthly  
- Run documentation generator to catch any drift
- Review example coverage for new patterns
- Update any outdated screenshots or diagrams

### Per Release
- Full documentation regeneration
- Example validation
- Completeness review
- Quality assurance checklist

## Troubleshooting Common Issues

### Documentation Generator Fails
- Check tool imports and dependencies
- Verify all tools have proper schema methods
- Review error messages for missing properties

### Examples Break
- Check for tool API changes
- Update examples to match current schemas
- Verify environment setup and dependencies

### Cross-References Break
- Check for moved or renamed files
- Update links in navigation files
- Verify relative path calculations

### Content Becomes Stale
- Focus on implementation-agnostic concepts
- Move implementation details to auto-generated sections
- Regular review and pruning of outdated information

---

*This process ensures our documentation remains valuable and current while minimizing maintenance overhead.*