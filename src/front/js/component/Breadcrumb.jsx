import React from "react";
import { Link } from "react-router-dom";
import "../../styles/breadcrumb.css";

export const Breadcrumb = ({ items = [], className = "" }) => {
    const normalizedItems = items.filter((item) => item?.label);

    if (normalizedItems.length === 0) {
        return null;
    }

    return (
        <nav
            aria-label="breadcrumb"
            className={`mw-breadcrumb ${className}`.trim()}
        >
            <ol className="mw-breadcrumb-list">
                {normalizedItems.map((item, index) => {
                    const isLast = index === normalizedItems.length - 1;

                    return (
                        <li className="mw-breadcrumb-item" key={`${item.label}-${index}`}>
                            {item.to && !isLast ? (
                                <Link className="mw-breadcrumb-link" to={item.to}>
                                    {item.label}
                                </Link>
                            ) : (
                                <span
                                    className={isLast ? "mw-breadcrumb-current" : "mw-breadcrumb-text"}
                                    aria-current={isLast ? "page" : undefined}
                                >
                                    {item.label}
                                </span>
                            )}
                        </li>
                    );
                })}
            </ol>
        </nav>
    );
};
