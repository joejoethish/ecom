---
inclusion: always
---

# Code Quality Standards

## Zero Error Policy

All code must be error-free before task completion. This applies to both TypeScript and Python codebases.

## TypeScript Requirements

- **Build validation**: Run `npm run build` after every TypeScript change
- **Type safety**: Fix all TypeScript compilation errors and warnings
- **Linting**: Ensure ESLint passes without errors
- **Import resolution**: Verify all imports resolve correctly
- **Component props**: Ensure all React component props are properly typed

## Python Requirements

- **Syntax validation**: Ensure all Python code is syntactically correct
- **Import resolution**: Verify all imports are available and correct
- **Django compatibility**: Ensure Django models, views, and serializers are properly structured
- **Type hints**: Use type hints where appropriate for better code clarity

## Validation Commands

### Frontend (TypeScript)
```bash
cd frontend
npm run build          # Must pass without errors
npm run lint           # Must pass without errors
npm run type-check     # Must pass without errors
```

### Backend (Python)
```bash
cd backend
python manage.py check          # Must pass without errors
python -m py_compile **/*.py    # Syntax validation
python manage.py migrate --dry-run  # Migration validation
```

## Error Resolution Priority

1. **Compilation errors**: Fix TypeScript/Python syntax errors first
2. **Type errors**: Resolve type mismatches and missing type definitions
3. **Import errors**: Fix missing or incorrect imports
4. **Linting errors**: Address code style and quality issues
5. **Runtime errors**: Test functionality to ensure no runtime failures

## Quality Gates

- No task is complete until all validation commands pass
- All code changes must maintain existing functionality
- New code must follow established patterns and conventions
- Error messages must be meaningful and actionable