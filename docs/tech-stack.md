# Technology Stack and Available Tools

This document outlines the technology stack and tools available for use for this project, emphasizing flexibility and optimal tool selection based on task requirements.

## Core Principle

**"Use whatever is best for the job, if it is available to run on the available hardware."**

This means:
- Choose the right tool for each specific task
- Performance, capability, and quality take precedence over arbitrary language consistency
- Cost matters, but project objectives override cost concerns
- Leverage available hardware capabilities fully (GPU, CPU cores, frameworks)
- Document new tools and integrate them into build/workflow systems

## Available Technology Stack

### Languages & Runtimes

| Language | Purpose | When to Use | Notes |
|----------|---------|------------|-------|
| **Python** 3.14.0+ | Data processing, scripts, ML pipelines | Default choice for rapid development, data workflows | Most mature ecosystem, extensive ML libraries |
| **Swift** | Native macOS/iOS, Apple framework integration | ML with Core ML/MLX, performance-critical native code | Preferred for on-device ML, best Apple framework access |
| **C/C++** | Performance-critical, compiled operations | Heavy numerical computing, signal processing | Excellent Apple framework bindings via Metal/Accelerate |
| **Node.js** 22.14.0+ | Workflow orchestration, BMAD execution | Workflow coordination, async I/O operations | Required for BMAD integration |
| **Zsh/Bash** | Shell workflows, orchestration glue | Build automation via Makefile targets | Use within Make for simple operations |
| **Objective-C** | Legacy Apple framework integration | Only if modern Swift/C++ alternatives insufficient | Avoid for new development |

### Package Management & Containerization

| Tool | Purpose | Status |
|------|---------|--------|
| **Homebrew** | MacOS package management | Primary tool for installing compiled tools |
| **Docker** | Containerized workflows, reproducibility | Available via Homebrew; use for isolated environments |
| **Python venv** | Python package isolation | Primary Python environment management |
| **Swift Package Manager** | Swift dependency management | Integrated with Xcode, use for Swift projects |
| **CMake** | C/C++ build system | Use for cross-platform compiled code |
| **npm** | Node.js package management | Required for BMAD and workflow tools |

### Apple Native Frameworks (First-Class Citizens)

When building Swift or Objective-C components, leverage these frameworks:

**Machine Learning**:
- **Core ML** - Model training and inference
- **Create ML** - Visual model training
- **Core ML Tools** - Format conversion and optimization
- **MLX** - Efficient ML on Apple Silicon
- **Metal** - GPU-accelerated compute

**Data Processing & Analysis**:
- **Vision** - Image analysis, OCR, object detection
- **Natural Language** - Text processing, entity extraction, sentiment analysis
- **Speech** - Audio transcription
- **Sound Analysis** - Audio classification and processing
- **Translation** - Multilingual support

**Numerical Computing**:
- **Accelerate** - SIMD vectorization, linear algebra
- **BNNS** (Basic Neural Network Subroutines) - Neural network building blocks

### AI/ML Tools & Services

**On-Device (Preferred)**:
1. **Apple Frameworks** - No cost, maximum privacy, GPU acceleration via Metal
2. **Ollama** - Local LLM inference, various models, no API limits

**Cloud/Subscription (When Local Insufficient)**:
3. **OpenAI Codex** - Code generation (subscription: GPT+)
4. **GitHub Copilot** - IDE integration (subscription: GitHub Pro, Copilot Pro+)
5. **OpenAI APIs** - GPT-4, GPT-4 Turbo, embeddings, fine-tuning (cost per token)

**Guidance**:
- Try Apple frameworks and Ollama first
- Escalate to external APIs only when capability, quality, or latency demands it
- Cost and API limits matter, but **never sacrifice project quality to save costs**

## Hardware Capabilities

**Reference Machine** (Mac Studio M2 Ultra):
- **CPU**: 24 cores (8 performance + 16 efficiency)
- **GPU**: 60 cores (Metal-compatible)
- **Memory**: 128 GB unified (can address all VRAM from CPU)
- **Bandwidth**: 200GB/s unified memory bandwidth

**ML Workload Recommendations**:
- **Up to 16GB**: Basic Python scripts, small models (<1B params)
- **16-64GB**: Medium models (1-7B params), full pipelines
- **64GB+**: Large models (13B+ params), batch inference
- **GPU via Metal**: ~2-5x speedup for typical ML operations vs CPU-only

## Architecture Guidelines

### When to Use Each Language

**Use Python for**:
- Data exploration and prototyping
- Pandas/NumPy data processing
- Hugging Face Transformers workflows
- Integration with existing Python libraries
- Most initial implementations

**Use Swift for**:
- Production ML inference (Core ML models)
- Native performance optimization
- Direct Apple framework integration
- macOS/iOS app components
- Memory-efficient on-device processing

**Use C/C++ for**:
- Signal processing and DSP
- High-throughput data transformations
- Numerical computing requiring SIMD
- Linking to specialized C/C++ libraries
- Performance-critical bottlenecks

**Use Node.js for**:
- Workflow orchestration
- Asynchronous workflow coordination

### Workflow Composition Strategy

Build composite workflows that mix languages:

```makefile
# Makefile example: Multi-language workflow
ml-pipeline:
	# Stage 1: Python data prep
	$(PY) source/preprocess.py --input $(INPUT) --output /tmp/preprocessed
	
	# Stage 2: Swift Core ML inference
	swift run ml-inference --input /tmp/preprocessed --output /tmp/results
	
	# Stage 3: C++ performance optimization (if needed)
	./build/optimize --input /tmp/results --output $(OUTPUT)
	
	# Stage 4: Validation (Python)
	$(PY) source/validate.py --output $(OUTPUT)
```

**Benefits**:
- Each stage uses the best tool for that job
- Clear interface boundaries (file-based I/O)
- Easy to test and debug each component
- Maintainable and understandable

## Adding New Tools & Languages

When you need a tool not currently in the stack:

1. **Verify availability on target hardware**: Can it run on macOS with available hardware?
2. **Installation method**: Via Homebrew, Xcode, direct download, or containerized?
3. **Integration**: How does it fit in Makefile/BMAD workflows?
4. **Documentation**: Update this file with tool purpose and usage
5. **Build automation**: Add targets to `Makefile` if used in workflows

Example (installing and integrating a new tool):

```bash
# Install
brew install your-new-tool

# Add to Makefile
.PHONY: your-workflow
your-workflow:
	your-new-tool --input $(INPUT) --output $(OUTPUT)

# Document in dev guide and this file
```

## Current Implementation Status

**Fully Integrated**:
- ✅ Python 3.14.0 (data processing, ML pipelines)
- ✅ Node.js 22.14.0 (BMAD orchestration)
- ✅ GNU Make 3.81+ (task automation)
- ✅ Zsh (shell execution)
- ✅ Homebrew (package management)
- ✅ BMAD Method 6.0.0-alpha.8 (AI-assisted workflows)

**Available (installable)**:
- ⏳ Swift (Xcode included, frameworks available)
- ⏳ C/C++ (via Homebrew: gcc, clang, cmake)
- ⏳ Docker (via Homebrew)
- ⏳ Ollama (via Homebrew)

**Partially Integrated**:
- ⏳ Apple Frameworks (Core ML, MLX, Vision, etc.) - usable but no example projects yet

**Future Additions**:
- Rust (for performance-critical safe systems code)
- CUDA/OpenCL (if GPU acceleration beyond Metal needed)
- Additional LLM frameworks as they mature

## Best Practices

### 1. Language Selection
- **Default to Python** for initial implementation (fastest to prototype)
- **Profile before optimizing** (measure where time is actually spent)
- **Only use compiled languages** if profiling shows bottleneck
- **Prefer Apple frameworks** over generic alternatives (better integration, fewer dependencies)

### 2. Build Integration
- All workflows must be callable from Makefile or BMAD menu
- File-based interfaces between language boundaries (ensures composability)
- Keep deployment dependencies documented
- Log which tool/version ran for reproducibility

### 3. Dependency Management
- Use language-native package managers (pip, npm, Swift PM, CMake)
- Document versions in project files (requirements.txt, package.json, Cargo.toml, etc.)
- Prefer Homebrew-installable tools over custom binaries
- Keep virtual environments isolated

### 4. Documentation
- Document tool choice rationale in code comments
- Update `docs/development-guide.md` when adding language patterns
- Maintain this file as reference for what's available
- Include language-specific gotchas in dev guide

---

**Status**: Active  
**Last Updated**: 2025-11-18  
**Principle**: Use whatever is best for the job ✅