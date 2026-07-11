"""DOM extraction utilities for ARES."""

from __future__ import annotations

from typing import Any

from selenium.webdriver.remote.webdriver import WebDriver


class DOMExtractor:
    """Extract visible and interactive DOM elements from the current page."""

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver

    def extract_visible_elements(self) -> list[dict[str, Any]]:
        """Return visible DOM elements with locators and geometry."""

        script = """
        const elements = Array.from(document.querySelectorAll('*'));

        function isVisible(element) {
            const style = window.getComputedStyle(element);
            const rect = element.getBoundingClientRect();

            return (
                style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                parseFloat(style.opacity || '1') > 0 &&
                rect.width > 0 &&
                rect.height > 0
            );
        }

        function isClickable(element) {
            const tag = element.tagName.toLowerCase();
            const role = element.getAttribute('role');
            const clickableTags = ['a', 'button', 'input', 'select', 'textarea', 'option'];

            return (
                clickableTags.includes(tag) ||
                role === 'button' ||
                role === 'link' ||
                typeof element.onclick === 'function' ||
                element.hasAttribute('onclick') ||
                element.tabIndex >= 0
            );
        }

        function buildXPath(element) {
            if (element.id) {
                return `//*[@id="${element.id}"]`;
            }

            const parts = [];

            while (element && element.nodeType === Node.ELEMENT_NODE) {
                let index = 1;
                let sibling = element.previousElementSibling;

                while (sibling) {
                    if (sibling.tagName === element.tagName) {
                        index += 1;
                    }

                    sibling = sibling.previousElementSibling;
                }

                const tagName = element.tagName.toLowerCase();
                parts.unshift(`${tagName}[${index}]`);
                element = element.parentElement;
            }

            return '/' + parts.join('/');
        }

        function escapeCss(value) {
            if (window.CSS && CSS.escape) {
                return CSS.escape(value);
            }

            return value.replace(/([^a-zA-Z0-9_-])/g, '\\\\$1');
        }

        function buildCssSelector(element) {
            if (element.id) {
                return `#${escapeCss(element.id)}`;
            }

            const parts = [];
            let current = element;

            while (current && current.nodeType === Node.ELEMENT_NODE) {
                let selector = current.tagName.toLowerCase();

                if (current.classList.length > 0) {
                    const classes = Array.from(current.classList)
                        .slice(0, 3)
                        .map(cls => `.${escapeCss(cls)}`)
                        .join('');

                    selector += classes;
                }

                const parent = current.parentElement;

                if (parent) {
                    const sameTagSiblings = Array.from(parent.children)
                        .filter(child => child.tagName === current.tagName);

                    if (sameTagSiblings.length > 1) {
                        const position = sameTagSiblings.indexOf(current) + 1;
                        selector += `:nth-of-type(${position})`;
                    }
                }

                parts.unshift(selector);

                if (current.id) {
                    break;
                }

                current = parent;
            }

            return parts.join(' > ');
        }

        return elements
            .filter(isVisible)
            .map((element, index) => {
                const rect = element.getBoundingClientRect();

                return {
                    index: index,
                    tag: element.tagName.toLowerCase(),
                    text: (element.innerText || element.value || '').trim().slice(0, 500),
                    id: element.id || '',
                    name: element.getAttribute('name') || '',
                    type: element.getAttribute('type') || '',
                    role: element.getAttribute('role') || '',
                    class_name: element.className && typeof element.className === 'string'
                        ? element.className
                        : '',
                    href: element.getAttribute('href') || '',
                    placeholder: element.getAttribute('placeholder') || '',
                    aria_label: element.getAttribute('aria-label') || '',
                    xpath: buildXPath(element),
                    css_selector: buildCssSelector(element),
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height,
                    center_x: rect.x + rect.width / 2,
                    center_y: rect.y + rect.height / 2,
                    visible: true,
                    enabled: !element.disabled,
                    clickable: isClickable(element)
                };
            });
        """

        elements = self.driver.execute_script(script)

        if not isinstance(elements, list):
            raise RuntimeError("DOM extraction did not return a list.")

        return elements

    def extract_interactive_elements(self) -> list[dict[str, Any]]:
        """Return only visible elements that can be interacted with."""

        elements = self.extract_visible_elements()

        return [
            element
            for element in elements
            if element.get("clickable") or element.get("tag") in {"input", "select", "textarea"}
        ]

    def get_element_at_point(self, x: float, y: float) -> dict[str, Any] | None:
        """Return DOM information for the element at viewport coordinates."""

        script = """
        const element = document.elementFromPoint(arguments[0], arguments[1]);

        if (!element) {
            return null;
        }

        const rect = element.getBoundingClientRect();

        return {
            tag: element.tagName.toLowerCase(),
            text: (element.innerText || element.value || '').trim().slice(0, 500),
            id: element.id || '',
            name: element.getAttribute('name') || '',
            type: element.getAttribute('type') || '',
            role: element.getAttribute('role') || '',
            class_name: element.className && typeof element.className === 'string'
                ? element.className
                : '',
            href: element.getAttribute('href') || '',
            placeholder: element.getAttribute('placeholder') || '',
            aria_label: element.getAttribute('aria-label') || '',
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            center_x: rect.x + rect.width / 2,
            center_y: rect.y + rect.height / 2,
            enabled: !element.disabled
        };
        """

        result = self.driver.execute_script(script, x, y)

        if result is None:
            return None

        if not isinstance(result, dict):
            raise RuntimeError("elementFromPoint did not return a DOM object.")

        return result