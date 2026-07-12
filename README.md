# ARES Conference Artifact

**ARES** is a research-grade autonomous web testing framework accompanying the conference paper:

> **ARES: An Autonomous End-to-End Web Test Generation Framework with Proactive Self-Healing**

This repository contains the complete experimental artifact used to demonstrate the framework pipeline described in the paper.

---

## Artifact Overview

ARES automatically explores modern web applications by combining browser automation, DOM analysis, state graph construction, action inference, oracle evaluation, and experiment reporting.

The current conference artifact demonstrates the complete autonomous execution pipeline on multiple web application subjects under test (SUTs).

---

## Framework Architecture

![ARES Architecture](docs/architecture.png)

---

## Repository Structure

```text
ARES-Conference-Artifact/

applications/
    angular/
    opencart/
    broadleaf/

runner/
    core/
    config/
    utils/

results/
evaluation/
docs/
```

---

## Current Implementation Status

| Module | Status |
|---------|--------|
| Browser Manager | ✅ |
| DOM Analyzer | ✅ |
| Action Executor | ✅ |
| State Graph Builder | ✅ |
| Logic Engine | ✅ |
| Oracle Engine | ✅ |
| Experiment Runner | ✅ |
| Evaluation Pipeline | ✅ |
| Report Generator | ✅ |

---

## Supported Subject Applications

| Application | Status |
|-------------|--------|
| Angular Demo Store | ✅ |
| OpenCart 3.0.3.8 | ✅ |
| Broadleaf Commerce | ✅ |


---

# Requirements

The artifact has been tested with the following environment:

| Component | Version |
|-----------|---------|
| Python | 3.12+ |
| Google Chrome | Latest Stable |
| ChromeDriver | Selenium Manager (automatic) |
| Node.js | 20+ |
| npm | 10+ |
| Docker Desktop | Latest |
| Git | Latest |

---

# Installation

Clone the repository:

```bash
git clone https://github.com/SDET-Hamad-KMughal/ARES-Conference-Artifact.git

cd ARES-Conference-Artifact
```

---

## Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Install Angular Dependencies

```bash
cd applications/angular/ares-angular-sut

npm install
```

Start Angular:

```bash
npm start
```

The application will be available at:

```
http://localhost:4200
```

---

## OpenCart

The Dockerized OpenCart application is located under:

```
applications/opencart/
```

Start using Docker Compose.

---

## Broadleaf Commerce

The Dockerized Broadleaf Commerce application is located under:

```
applications/broadleaf/
```

Start using Docker Compose.

Default URL:

```
https://localhost:8443
```

---

# Quick Start

Run each module independently.

## Browser Manager

```bash
python -m runner.test_browser_manager
```

---

## DOM Analyzer

```bash
python -m runner.test_dom_analyzer
```

---

## State Graph Builder

```bash
python -m runner.test_state_graph
```

---

## Logic Engine

```bash
python -m runner.test_logic_engine
```

---

## Oracle Engine

```bash
python -m runner.test_oracle_engine
```

---

## Experiment Runner

```bash
python -m runner.test_experiment_runner
```

---

## Evaluation Pipeline

```bash
python -m runner.test_evaluation_pipeline
```

---

## Report Generator

```bash
python -m runner.test_report_generator
```

---

# Expected Outputs

Successful execution produces the following artifacts:

```
runner/results/

angular/
    browser/
    dom_analysis.json
    state_graph.json
    experiment/
        angular_route_exploration_result.json
    evaluation/
        angular_route_exploration_evaluation.json
    report/
        evaluation_report.txt
```

These outputs document every stage of the autonomous testing pipeline.

---

# Reproducing the Conference Evaluation

1. Start the target application (Angular, OpenCart, or Broadleaf).
2. Run the Experiment Runner.

```bash
python -m runner.test_experiment_runner
```

3. Compute evaluation metrics.

```bash
python -m runner.test_evaluation_pipeline
```

4. Generate the artifact report.

```bash
python -m runner.test_report_generator
```

The generated report summarizes execution statistics, state exploration, oracle results, and overall experiment quality.

---

# Experimental Workflow

```
Start SUT
     │
     ▼
Browser Manager
     │
     ▼
DOM Analyzer
     │
     ▼
Action Executor
     │
     ▼
State Graph Builder
     │
     ▼
Logic Engine
     │
     ▼
Oracle Engine
     │
     ▼
Experiment Runner
     │
     ▼
Evaluation Pipeline
     │
     ▼
Conference Report
```

---

# Research Purpose

This repository accompanies the ARES conference paper and demonstrates a lightweight, research-grade implementation of the proposed autonomous web testing framework.

The artifact focuses on:

- Autonomous browser interaction
- DOM analysis
- State graph construction
- Action inference
- Oracle-based validation
- End-to-end experiment execution
- Automated evaluation
- Reproducible reporting

---

# License

This repository is released for research and academic purposes.

---

# Citation

If you use this artifact in your research, please cite the accompanying ARES conference paper.

```bibtex
@inproceedings{ARES2026,
  title={ARES: An Autonomous End-to-End Web Test Generation Framework with Proactive Self-Healing},
  author={Mughal, Hamad Sajad},
  year={2026}
}
```