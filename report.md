# 🌸 Code Quality Analysis Report 🌸

## Overall Assessment

- **Quality Score**: 38.50/100
- **Quality Level**: 😐 Slightly stinky youth - A faint whiff, open a window and hope for the best.
- **Analyzed Files**: 68
- **Total Lines**: 20562

## Quality Metrics

| Metric | Score | Weight | Status |
|------|------|------|------|
| State Management | 17.62 | 0.20 | ✓✓ |
| Error Handling | 25.00 | 0.10 | ✓ |
| Comment Ratio | 27.75 | 0.15 | ✓ |
| Code Structure | 30.00 | 0.15 | ✓ |
| Code Duplication | 35.00 | 0.15 | ○ |
| Cyclomatic Complexity | 68.30 | 0.30 | ⚠ |

## Problem Files (Top 5)

### 1. /home/runner/work/CABM/CABM/utils/RAG/Reranker/Reranker_Model.py (Score: 57.10)
**Issue Categories**: 📝 Comment Issues:1

**Main Issues**:
- Code comment ratio is extremely low (0.00%), almost no comments

### 2. /home/runner/work/CABM/CABM/routes/story_routes.py (Score: 56.05)
**Issue Categories**: 🔄 Complexity Issues:8, 📝 Comment Issues:1, ⚠️ Other Issues:4

**Main Issues**:
- Code comment ratio is low (9.28%), consider adding more comments
- Function list_stories has very high cyclomatic complexity (19), consider refactoring
- Function create_story has very high cyclomatic complexity (44), consider refactoring
- Function story_chat_stream has very high cyclomatic complexity (37), consider refactoring
- Function generate has very high cyclomatic complexity (31), consider refactoring
- Function 'list_stories' () is too long (81 lines), consider splitting
- Function 'list_stories' () complexity is severely high (19), must be simplified
- Function 'create_story' () is extremely long (211 lines), must be split
- Function 'create_story' () complexity is severely high (44), must be simplified
- Function 'story_chat_stream' () is extremely long (209 lines), must be split
- Function 'story_chat_stream' () complexity is severely high (37), must be simplified
- Function 'generate' () is extremely long (172 lines), must be split
- Function 'generate' () complexity is severely high (31), must be simplified

### 3. /home/runner/work/CABM/CABM/routes/chat_routes.py (Score: 53.70)
**Issue Categories**: 🔄 Complexity Issues:7, 📝 Comment Issues:1, ⚠️ Other Issues:5

**Main Issues**:
- Function 'chat_page' () is rather long (61 lines), consider refactoring
- Function 'chat_page' () complexity is high (17), consider simplifying
- Function 'chat_stream' () is too long (113 lines), consider splitting
- Function 'chat_stream' () complexity is severely high (24), must be simplified
- Function 'generate' () is too long (93 lines), consider splitting
- Function 'generate' () complexity is severely high (21), must be simplified
- Function 'get_initial_background' () is rather long (49 lines), consider refactoring
- Function 'add_background' () is rather long (59 lines), consider refactoring
- Code comment ratio is low (9.68%), consider adding more comments
- Function chat_page has very high cyclomatic complexity (17), consider refactoring
- Function chat_stream has very high cyclomatic complexity (24), consider refactoring
- Function generate has very high cyclomatic complexity (21), consider refactoring
- Function add_background has high cyclomatic complexity (12), consider simplifying

### 4. /home/runner/work/CABM/CABM/routes/multi_character_routes.py (Score: 49.53)
**Issue Categories**: 🔄 Complexity Issues:2, ⚠️ Other Issues:3

**Main Issues**:
- Function handle_next_speaker_recursively has very high cyclomatic complexity (36), consider refactoring
- Function 'handle_next_speaker_recursively' () is extremely long (217 lines), must be split
- Function 'handle_next_speaker_recursively' () complexity is severely high (36), must be simplified
- Function 'generate_options_after_recursion' () is rather long (62 lines), consider refactoring
- Function 'multi_character_chat_stream' () is rather long (63 lines), consider refactoring

### 5. /home/runner/work/CABM/CABM/services/multi_character_service.py (Score: 49.06)
**Issue Categories**: 🔄 Complexity Issues:6, ⚠️ Other Issues:3

**Main Issues**:
- Function format_messages_for_character has very high cyclomatic complexity (32), consider refactoring
- Function build_character_system_prompt has very high cyclomatic complexity (22), consider refactoring
- Function call_director_model has very high cyclomatic complexity (17), consider refactoring
- Function 'format_messages_for_character' () is extremely long (130 lines), must be split
- Function 'format_messages_for_character' () complexity is severely high (32), must be simplified
- Function 'build_character_system_prompt' () is too long (105 lines), consider splitting
- Function 'build_character_system_prompt' () complexity is severely high (22), must be simplified
- Function 'call_director_model' () is extremely long (121 lines), must be split
- Function 'call_director_model' () complexity is high (17), consider simplifying

## Improvement Suggestions

### High Priority
- Keep up the clean code standards, don't let the mess creep in

### Medium Priority
- Go further—optimize for performance and readability, just because you can
- Polish your docs and comments, make your team love you even more

