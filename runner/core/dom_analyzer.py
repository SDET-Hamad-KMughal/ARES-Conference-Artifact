"""ARES DOM analysis component.

This module converts the current Selenium browser page into a structured JSON
representation containing page metadata, interactive elements, selectors,
XPath expressions, forms, and element geometry.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class DOMAnalyzer:
    """
    Extract structured information from the current Selenium browser page.

    The generated representation can later be consumed by the ARES state graph,
    logic engine, oracle engine, and experiment runner.
    """

    def __init__(self, driver: Any) -> None:
        """
        Initialize the analyzer with an active Selenium WebDriver.

        Args:
            driver: Active Selenium WebDriver instance.
        """
        self.driver = driver
        self._analysis: Dict[str, Any] | None = None

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze the current page.

        Returns:
            A structured dictionary containing page metadata, buttons, links,
            inputs, forms, selectors, XPath expressions, and summary counts.

        Raises:
            RuntimeError: If the JavaScript analysis does not return a result.
        """

        analysis = self.driver.execute_script(
            r"""
            return (() => {
                function isVisible(element) {
                    if (!element) {
                        return false;
                    }

                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();

                    return (
                        style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        Number(style.opacity) !== 0 &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                }

                function isEnabled(element) {
                    return (
                        !element.disabled &&
                        element.getAttribute("aria-disabled") !== "true"
                    );
                }

                function buildCssSelector(element) {
                    if (
                        !element ||
                        element.nodeType !== Node.ELEMENT_NODE
                    ) {
                        return null;
                    }

                    if (element.id) {
                        return `#${CSS.escape(element.id)}`;
                    }

                    const selectorParts = [];
                    let current = element;

                    while (
                        current &&
                        current.nodeType === Node.ELEMENT_NODE
                    ) {
                        let selector = current.tagName.toLowerCase();

                        if (current.classList.length > 0) {
                            selector += "." +
                                Array.from(current.classList)
                                    .map(className =>
                                        CSS.escape(className)
                                    )
                                    .join(".");
                        }

                        const parent = current.parentElement;

                        if (parent) {
                            const sameTagSiblings =
                                Array.from(parent.children).filter(
                                    sibling =>
                                        sibling.tagName === current.tagName
                                );

                            if (sameTagSiblings.length > 1) {
                                const index =
                                    sameTagSiblings.indexOf(current) + 1;

                                selector +=
                                    `:nth-of-type(${index})`;
                            }
                        }

                        selectorParts.unshift(selector);

                        if (current === document.body) {
                            break;
                        }

                        current = parent;
                    }

                    return selectorParts.join(" > ");
                }

                function xpathLiteral(value) {
                    if (!value.includes("'")) {
                        return `'${value}'`;
                    }

                    if (!value.includes('"')) {
                        return `"${value}"`;
                    }

                    const parts = value.split("'");

                    return (
                        "concat(" +
                        parts
                            .map((part, index) => {
                                const quotedPart = `'${part}'`;

                                if (index === parts.length - 1) {
                                    return quotedPart;
                                }

                                return `${quotedPart}, "'", `;
                            })
                            .join("") +
                        ")"
                    );
                }

                function buildXPath(element) {
                    if (
                        !element ||
                        element.nodeType !== Node.ELEMENT_NODE
                    ) {
                        return null;
                    }

                    if (element.id) {
                        return `//*[@id=${xpathLiteral(element.id)}]`;
                    }

                    const xpathParts = [];
                    let current = element;

                    while (
                        current &&
                        current.nodeType === Node.ELEMENT_NODE
                    ) {
                        const tagName =
                            current.tagName.toLowerCase();

                        if (current === document.documentElement) {
                            xpathParts.unshift(tagName);
                            break;
                        }

                        const parent = current.parentElement;
                        let xpathPart = tagName;

                        if (parent) {
                            const sameTagSiblings =
                                Array.from(parent.children).filter(
                                    sibling =>
                                        sibling.tagName === current.tagName
                                );

                            if (sameTagSiblings.length > 1) {
                                const index =
                                    sameTagSiblings.indexOf(current) + 1;

                                xpathPart += `[${index}]`;
                            }
                        }

                        xpathParts.unshift(xpathPart);
                        current = parent;
                    }

                    return "/" + xpathParts.join("/");
                }

                function getAttributes(element) {
                    return Object.fromEntries(
                        Array.from(element.attributes).map(
                            attribute => [
                                attribute.name,
                                attribute.value
                            ]
                        )
                    );
                }

                function getText(element) {
                    return (
                        element.innerText ||
                        element.textContent ||
                        element.value ||
                        ""
                    ).trim();
                }

                function getBoundingBox(element) {
                    const rect = element.getBoundingClientRect();

                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        right: rect.right,
                        bottom: rect.bottom,
                        left: rect.left
                    };
                }

                function baseElementData(element) {
                    return {
                        tag: element.tagName.toLowerCase(),
                        id: element.id || null,
                        name: element.getAttribute("name"),
                        text: getText(element),
                        classes: Array.from(element.classList),
                        css_selector: buildCssSelector(element),
                        xpath: buildXPath(element),
                        visible: isVisible(element),
                        enabled: isEnabled(element),
                        attributes: getAttributes(element),
                        bounding_box: getBoundingBox(element)
                    };
                }

                const buttons = Array.from(
                    document.querySelectorAll(
                        [
                            "button",
                            "input[type='button']",
                            "input[type='submit']",
                            "input[type='reset']",
                            "[role='button']"
                        ].join(", ")
                    )
                ).map(element => ({
                    ...baseElementData(element),
                    type:
                        element.getAttribute("type") || null,
                    value:
                        "value" in element
                            ? element.value || null
                            : null
                }));

                const links = Array.from(
                    document.querySelectorAll("a[href]")
                ).map(element => ({
                    ...baseElementData(element),
                    href: element.href || null,
                    raw_href:
                        element.getAttribute("href"),
                    target:
                        element.getAttribute("target"),
                    rel:
                        element.getAttribute("rel")
                }));

                const inputs = Array.from(
                    document.querySelectorAll(
                        "input, textarea, select"
                    )
                ).map(element => ({
                    ...baseElementData(element),
                    type:
                        element.getAttribute("type") ||
                        element.tagName.toLowerCase(),
                    placeholder:
                        element.getAttribute("placeholder"),
                    value:
                        "value" in element
                            ? element.value || null
                            : null,
                    required:
                        Boolean(element.required),
                    readonly:
                        Boolean(element.readOnly),
                    checked:
                        "checked" in element
                            ? Boolean(element.checked)
                            : null,
                    autocomplete:
                        element.getAttribute("autocomplete"),
                    aria_label:
                        element.getAttribute("aria-label")
                }));

                const forms = Array.from(
                    document.querySelectorAll("form")
                ).map(form => {
                    const containedInputs = Array.from(
                        form.querySelectorAll(
                            "input, textarea, select"
                        )
                    );

                    return {
                        ...baseElementData(form),
                        action:
                            form.action || null,
                        raw_action:
                            form.getAttribute("action"),
                        method:
                            (form.method || "get").toUpperCase(),
                        enctype:
                            form.enctype || null,
                        input_count:
                            containedInputs.length,
                        inputs:
                            containedInputs.map(input => ({
                                id:
                                    input.id || null,
                                name:
                                    input.getAttribute("name"),
                                type:
                                    input.getAttribute("type") ||
                                    input.tagName.toLowerCase(),
                                css_selector:
                                    buildCssSelector(input),
                                xpath:
                                    buildXPath(input)
                            }))
                    };
                });

                const interactiveElements = Array.from(
                    document.querySelectorAll(
                        [
                            "button",
                            "a[href]",
                            "input",
                            "textarea",
                            "select",
                            "[role='button']",
                            "[onclick]",
                            "[tabindex]"
                        ].join(", ")
                    )
                ).map(baseElementData);

                return {
                    title: document.title,
                    url: window.location.href,
                    page_source_length:
                        document.documentElement.outerHTML.length,
                    buttons: buttons,
                    links: links,
                    inputs: inputs,
                    forms: forms,
                    interactive_elements:
                        interactiveElements,
                    summary: {
                        button_count:
                            buttons.length,
                        link_count:
                            links.length,
                        input_count:
                            inputs.length,
                        form_count:
                            forms.length,
                        interactive_element_count:
                            interactiveElements.length
                    }
                };
            })();
            """
        )

        if analysis is None:
            raise RuntimeError(
                "DOM analysis returned no result."
            )

        analysis["timestamp"] = datetime.now(
            timezone.utc
        ).isoformat()

        self._analysis = analysis
        return self._analysis

    def save_json(self, output_path: str | Path) -> Path:
        """
        Save the latest DOM analysis as formatted JSON.

        Args:
            output_path: Destination JSON path.

        Returns:
            Resolved output path.

        Raises:
            RuntimeError: If analyze() has not been called.
        """

        if self._analysis is None:
            raise RuntimeError(
                "No DOM analysis is available. "
                "Call analyze() before save_json()."
            )

        path = Path(output_path)
        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with path.open(
            "w",
            encoding="utf-8"
        ) as output_file:
            json.dump(
                self._analysis,
                output_file,
                indent=2,
                ensure_ascii=False
            )

        return path