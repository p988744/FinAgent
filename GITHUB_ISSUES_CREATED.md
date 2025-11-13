# GitHub Issues Created - 2025-11-13

All unimplemented features have been documented as GitHub issues for tracking and collaboration.

## 📊 Overview

- **Total Issues:** 7
- **Milestones:** 3 (v0.1.0, v0.2.0, v0.3.0)
- **Labels:** priority:high, priority:medium, priority:low, good-first-issue, help-wanted

## 🎯 Milestone: v0.1.0 - Essential Features

**Goal:** Polish release with history persistence and export features

### Issue #2: Implement Query History Persistence to Database
- **Priority:** 🔴 HIGH
- **Labels:** enhancement, priority:high
- **Effort:** 2-3 hours
- **Status:** 60% complete (database ready, needs CLI integration)
- **Link:** https://github.com/p988744/FinAgent/issues/2

### Issue #3: Implement Export Results Functionality (/export)
- **Priority:** 🟡 MEDIUM
- **Labels:** enhancement, priority:medium, good-first-issue
- **Effort:** 1-2 hours
- **Status:** 10% complete (command exists, needs implementation)
- **Link:** https://github.com/p988744/FinAgent/issues/3

## 🎯 Milestone: v0.2.0 - UX Improvements

**Goal:** Statistics and health check enhancements

### Issue #4: Implement Statistics Command (/stats)
- **Priority:** 🟢 LOW
- **Labels:** enhancement, priority:low, good-first-issue
- **Effort:** 1 hour
- **Status:** Database methods exist, needs CLI command
- **Link:** https://github.com/p988744/FinAgent/issues/4

### Issue #5: Enhance Health Check Endpoint with Dependency Checks
- **Priority:** 🟢 LOW
- **Labels:** enhancement, priority:low
- **Effort:** 2 hours
- **Status:** 40% complete (basic endpoint exists)
- **Link:** https://github.com/p988744/FinAgent/issues/5

## 🎯 Milestone: v0.3.0 - Polish & Platform Compatibility

**Goal:** Polish features and cross-platform support

### Issue #6: Add Citation Details Command (/cite <編號>)
- **Priority:** 🟢 LOW
- **Labels:** enhancement, priority:low, good-first-issue
- **Effort:** 30 minutes
- **Status:** Minor UX improvement
- **Link:** https://github.com/p988744/FinAgent/issues/6

### Issue #7: Add Session Management for Query History
- **Priority:** 🟢 LOW
- **Labels:** enhancement, priority:low
- **Effort:** 2 hours
- **Status:** Database schema ready, needs implementation
- **Link:** https://github.com/p988744/FinAgent/issues/7

### Issue #8: Add Windows Support for ESC Key Query Cancellation
- **Priority:** 🟢 LOW
- **Labels:** enhancement, priority:low, help-wanted
- **Effort:** 2-3 hours (requires Windows testing)
- **Status:** Works on macOS/Linux only
- **Link:** https://github.com/p988744/FinAgent/issues/8

## 📋 Quick Commands

### View All Issues
```bash
gh issue list
```

### View by Milestone
```bash
gh issue list --milestone "v0.1.0"
gh issue list --milestone "v0.2.0"
gh issue list --milestone "v0.3.0"
```

### View by Priority
```bash
gh issue list --label "priority: high"
gh issue list --label "priority: medium"
gh issue list --label "priority: low"
```

### View Good First Issues
```bash
gh issue list --label "good first issue"
```

### View Help Wanted
```bash
gh issue list --label "help wanted"
```

## 🚀 Development Workflow

### Working on an Issue

1. **Assign yourself:**
   ```bash
   gh issue develop <issue-number> --checkout
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/issue-<number>-description
   ```
   Example: `git checkout -b feature/issue-2-query-history-persistence`

3. **Work on the feature:**
   - Make changes
   - Write tests
   - Update documentation

4. **Commit with reference:**
   ```bash
   git commit -m "feat: implement query history persistence (#2)"
   ```

5. **Push and create PR:**
   ```bash
   git push origin feature/issue-2-query-history-persistence
   gh pr create --fill
   ```

6. **Link PR to issue:**
   - PR description should include: "Closes #2"
   - Issue will auto-close when PR is merged

### Starting with Good First Issues

Recommended for new contributors:
- **Issue #3:** Export Results Functionality (1-2 hours)
- **Issue #4:** Statistics Command (1 hour)
- **Issue #6:** Citation Details Command (30 minutes)

## 📈 Progress Tracking

### Current Status
- **System Completion:** ~85%
- **Core Features:** ✅ Complete
- **Polish Features:** 🔄 7 issues remaining

### Recommended Implementation Order

**Week 1 (Essential):**
1. Issue #2: Query History Persistence (HIGH priority)
2. Issue #3: Export Results (MEDIUM priority)

**Week 2 (Nice-to-have):**
3. Issue #4: Statistics Command
4. Issue #5: Health Check Enhancements

**Week 3 (Polish):**
5. Issue #6: Citation Details
6. Issue #7: Session Management
7. Issue #8: Windows Support

## 🏷️ Label Guide

- **priority:high** - Critical features, implement first
- **priority:medium** - Important features, implement after high priority
- **priority:low** - Nice-to-have features, implement when time permits
- **good first issue** - Suitable for new contributors (1-2 hours, clear scope)
- **help wanted** - Community help needed (e.g., Windows testing)
- **enhancement** - New feature or improvement
- **bug** - Something isn't working (none currently)
- **documentation** - Documentation improvements

## 📚 References

- [UNIMPLEMENTED_FEATURES.md](UNIMPLEMENTED_FEATURES.md) - Detailed feature documentation
- [CLAUDE.md](CLAUDE.md) - Project architecture and guidelines
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - Full project specification

## 🤝 Contributing

1. Pick an issue from the list
2. Comment on the issue to claim it
3. Follow the development workflow above
4. Submit a PR with tests and documentation
5. Wait for review and merge

For questions, open a discussion or comment on the relevant issue.

---

**Last Updated:** 2025-11-13
**Issues Created:** 7
**Milestones:** 3
