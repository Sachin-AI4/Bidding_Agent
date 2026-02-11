# requirements.txt - Dependency Management

## Purpose
This file specifies all Python package dependencies required to run the Domain Auction Strategy AI system. It ensures reproducible installations and manages version compatibility across the multi-agent pipeline components.

## Core Dependencies

### pydantic>=2.0.0
**Purpose**: Runtime data validation and serialization
**Why Required**: 
- Validates AuctionContext, StrategyDecision, and other data models
- Provides type hints and automatic validation
- Enables JSON schema generation for API documentation
- Critical for data integrity throughout the pipeline

**Used In**: models.py, all components that process structured data

### langgraph>=0.1.0
**Purpose**: Orchestrates the multi-agent decision pipeline
**Why Required**:
- Provides StateGraph for workflow definition
- Manages node execution and state transitions
- Enables conditional routing based on processing results
- Core framework for the 4-layer decision pipeline

**Used In**: strategy_graph.py, graph_nodes.py

### langchain-anthropic>=0.1.0
**Purpose**: Integration with Anthropic Claude models
**Why Required**:
- Enables LLM-based strategy reasoning in Layer 2
- Provides structured prompt engineering
- Handles API authentication and rate limiting
- Supports Claude's advanced reasoning capabilities

**Used In**: llm_strategy.py (when anthropic provider selected)

### anthropic>=0.7.0
**Purpose**: Direct Anthropic API client
**Why Required**:
- Lower-level Claude integration for maximum flexibility
- Supports latest Claude models and features
- Enables custom prompt formatting and response parsing
- Provides direct access to Anthropic's API

**Used In**: llm_strategy.py (anthropic provider implementation)

### openai>=1.0.0
**Purpose**: OpenAI GPT model integration
**Why Required**:
- Alternative LLM provider for strategy reasoning
- Supports GPT-4 and other OpenAI models
- Enables provider switching without code changes
- Provides access to OpenAI's model ecosystem

**Used In**: llm_strategy.py (openai provider implementation)

### typing-extensions>=4.5.0
**Purpose**: Enhanced type hints for older Python versions
**Why Required**:
- Enables TypedDict usage in AuctionState
- Provides Literal types for strategy enumeration
- Supports advanced type annotations
- Ensures compatibility across Python versions

**Used In**: models.py, graph_nodes.py

## Optional Dependencies

### pytest>=7.0.0 (Development)
**Purpose**: Unit and integration testing framework
**Why Optional**:
- Only needed for running test suite
- Not required for production deployment
- Enables automated testing of decision pipeline
- Supports test discovery and reporting

**Used In**: test_strategy_system.py and potential unit tests

### pytest-asyncio>=0.21.0 (Development)
**Purpose**: Async testing support for pytest
**Why Optional**:
- Enables testing of async LangGraph operations
- Supports concurrent execution testing
- Only needed for comprehensive test coverage
- Not required for basic functionality

**Used In**: Advanced testing scenarios

## Installation Commands

### Basic Installation
```bash
pip install -r requirements.txt
```

### Development Installation
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio  # For testing
```

### Minimal Production Installation
```bash
pip install pydantic langgraph langchain-anthropic anthropic typing-extensions
```

## Version Constraints

### Why Specific Versions?
- **pydantic>=2.0.0**: Requires V2 for improved validation performance
- **langgraph>=0.1.0**: Minimum version with StateGraph support
- **anthropic>=0.7.0**: Supports latest Claude API features
- **openai>=1.0.0**: Modern OpenAI SDK with improved async support

### Compatibility Considerations
- **Python Version**: Requires Python 3.8+ for TypedDict support
- **Platform Support**: Cross-platform (Windows, macOS, Linux)
- **Dependency Conflicts**: Managed through version specifications

## Environment Setup

### API Keys Required
```bash
# For Anthropic Claude (recommended)
export ANTHROPIC_API_KEY="your-key-here"

# Or for OpenAI GPT
export OPENAI_API_KEY="your-key-here"
```

### Virtual Environment
```bash
python -m venv auction_strategy_env
source auction_strategy_env/bin/activate  # On Windows: auction_strategy_env\Scripts\activate
pip install -r requirements.txt
```

## Troubleshooting

### Common Issues

#### Import Errors
**Problem**: `ModuleNotFoundError` for pydantic or langgraph
**Solution**: Ensure all dependencies installed with `pip install -r requirements.txt`

#### API Key Missing
**Problem**: LLM features fail without API keys
**Solution**: Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables

#### Version Conflicts
**Problem**: Dependency resolution fails
**Solution**: Use virtual environment or update pip: `pip install --upgrade pip`

### Performance Notes
- **Installation Size**: ~50MB with all dependencies
- **Memory Usage**: ~100MB baseline for loaded models
- **API Costs**: LLM calls incur usage costs (monitor via performance stats)

## Security Considerations
- **API Keys**: Never commit to version control
- **Environment Variables**: Use secure key management in production
- **Dependencies**: Regularly update for security patches
- **Network**: LLM calls require internet access

This requirements file ensures the complete Domain Auction Strategy AI system can be reliably installed and run across different environments with all necessary dependencies properly managed.





