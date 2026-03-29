# Contributing to Project Pantheon 🏛️

Thank you for your interest in contributing! This guide will help you get started.

---

## 🎯 Quick Start

### 1. Fork and Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR_USERNAME/Pantheon.git
cd Pantheon
git remote add upstream https://github.com/Pranava-Kumar/Pantheon.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install pytest pytest-cov black flake8 isort
```

### 3. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

---

## 📝 Development Guidelines

### Code Style

We follow the **Google Python Style Guide**:

- **Indentation:** 4 spaces (no tabs)
- **Line Length:** Max 100 characters
- **Imports:** Grouped (stdlib → third-party → local)
- **Naming:** 
  - Modules: `snake_case.py`
  - Functions: `snake_case()`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Pre-Commit Checks

Before committing, run:

```bash
# Format code
black pantheon/ tests/
isort pantheon/ tests/

# Lint
flake8 pantheon/ tests/ --max-line-length=100

# Run tests
pytest tests/ -v

# Check test coverage (target: >85%)
pytest tests/ --cov=pantheon --cov-report=term-missing
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add Ollama LLM extractor
fix: Correct RSI calculation edge case
docs: Update README with free tier deployment guide
test: Add tests for fundamental scoring
refactor: Simplify MMCI weight update logic
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_mmci_scoring.py -v

# With coverage
pytest tests/ --cov=pantheon --cov-report=html
# Open htmlcov/index.html in browser
```

### Writing Tests

1. **Test files:** `tests/test_<module>.py`
2. **Test functions:** `def test_<functionality>():`
3. **Use fixtures** for common setup
4. **Assert clearly:** `assert result == expected`

Example:
```python
def test_compute_fundamental_score_strong():
    """Test fundamental scoring with strong company metrics."""
    data = {
        "roe": 20,
        "revenue_growth": 15,
    }
    score = compute_fundamental_score(data)
    assert 0.2 <= score <= 0.5  # Reasonable range for strong metrics
```

---

## 🐛 Reporting Bugs

### Before Reporting

1. Search existing issues
2. Check if bug exists on `main` branch
3. Gather information (logs, stack traces)

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what's wrong.

**To Reproduce**
Steps to reproduce:
1. Run `python -m pantheon.jobs.daily_analysis`
2. See error

**Expected behavior**
What should happen.

**Logs**
```
Error traceback here
```

**Environment:**
- OS: Windows 11
- Python: 3.11.9
- Version: main branch
```

---

## 💡 Feature Requests

### Before Requesting

1. Check existing feature requests
2. Ensure it aligns with project goals (free/open-source trading analysis)
3. Consider implementation complexity

### Feature Request Template

```markdown
**Problem Statement**
What problem does this solve?

**Proposed Solution**
How should it work?

**Alternatives Considered**
Other approaches you've thought about.

**Free/Open-Source Requirement**
Confirm this can be implemented with free tools/APIs.

**Additional Context**
Screenshots, mockups, references.
```

---

## 🔧 Pull Request Process

### 1. Update Documentation

- Update README.md if adding features
- Add docstrings to new functions
- Update `.env.example` if adding config

### 2. Update Tests

- Add tests for new functionality
- Ensure all tests pass: `pytest tests/ -v`
- Maintain >85% coverage

### 3. Request Review

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create PR on GitHub
# Link related issues: "Closes #123"
```

### 4. Address Feedback

- Respond to reviewer comments
- Make requested changes
- Re-request review

---

## 📚 Areas Needing Contribution

### High Priority

1. **Backtesting Framework** - Historical signal replay, P&L calculation
2. **Free LLM Integration** - Ollama, HuggingFace local models
3. **Monitoring Dashboard** - Grafana/Prometheus setup for free tier
4. **Docker Setup** - Containerization for easy deployment

### Medium Priority

1. **Enhanced News Sentiment** - Indian news sources (Moneycontrol, ET)
2. **Sector Analysis** - Nifty sector indices integration
3. **Options Chain Analysis** - NSE options data integration
4. **Portfolio Optimization** - Modern Portfolio Theory implementation

### Nice to Have

1. **Mobile App** - React Native dashboard
2. **Telegram Bot** - Signal notifications
3. **Export to Excel** - Report generation
4. **Multi-language Support** - Hindi, Tamil documentation

---

## 🆓 Free Tier Focus

**Important:** All contributions must use **free and open-source** tools:

✅ **Allowed:**
- Gemini Free Tier (60 req/min)
- Groq Free Tier (30 req/min)
- SQLite / Neon PostgreSQL (0.5GB free)
- Redis Cloud (30MB free)
- Streamlit Cloud (free hosting)
- GitHub Actions (2000 min/month free)

❌ **Not Allowed:**
- Paid API subscriptions
- Proprietary software dependencies
- Services without free tier

---

## 📞 Getting Help

- **Discussions:** [GitHub Discussions](https://github.com/Pranava-Kumar/Pantheon/discussions)
- **Issues:** [GitHub Issues](https://github.com/Pranava-Kumar/Pantheon/issues)
- **Discord:** [Link if available]

---

## 🎓 Learning Resources

### Python
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Real Python](https://realpython.com)
- [Python Testing with pytest](https://docs.pytest.org/)

### Trading
- [Investopedia](https://investopedia.com)
- [NSE India Learning](https://www.nseindia.com/learn)
- [Quantitative Trading (Ernest Chan)](https://epchan.blogspot.com)

### AI/ML
- [LangChain Docs](https://python.langchain.com)
- [HuggingFace Course](https://huggingface.co/course)
- [Groq Documentation](https://console.groq.com/docs)

---

## 🏆 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- Annual contributor highlights

---

## 📜 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers
- Stay on topic in discussions

---

**Thank you for contributing to Project Pantheon! 🎉**

Together, we're building the best **free and open-source** trading analysis platform for Indian markets.
