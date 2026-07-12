\# ARES Architecture



ARES follows a modular autonomous web-testing pipeline.



```text

Subject Application

&#x20;       │

&#x20;       ▼

Browser Manager

&#x20;       │

&#x20;       ▼

DOM Analyzer

&#x20;       │

&#x20;       ▼

Logic Engine

&#x20;       │

&#x20;       ▼

Action Executor

&#x20;       │

&#x20;       ▼

Oracle Engine

&#x20;       │

&#x20;       ▼

State Graph Builder

&#x20;       │

&#x20;       ▼

Experiment Runner

&#x20;       │

&#x20;       ▼

Evaluation Pipeline

&#x20;       │

&#x20;       ▼

Report Generator

```



\## Components



\### Browser Manager



Controls Selenium browser sessions and captures page artifacts.



\### DOM Analyzer



Extracts page metadata, interactive elements, selectors, XPath expressions,

attributes, and element geometry.



\### Logic Engine



Converts analyzed DOM elements into ranked candidate actions.



\### Action Executor



Executes browser actions such as clicks and form interaction.



\### Oracle Engine



Evaluates URL expectations, success evidence, and error indicators.



\### State Graph Builder



Represents observed application states as nodes and actions as directed edges.



\### Experiment Runner



Coordinates the complete ARES workflow across a configured route sequence.



\### Evaluation Pipeline



Calculates execution, action, graph, oracle, and quality metrics.



\### Report Generator



Produces a human-readable conference artifact evaluation report.

