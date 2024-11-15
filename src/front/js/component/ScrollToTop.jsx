import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";

const ScrollToTop = () => {
    const { pathname } = useLocation();

    useEffect(() => {
        const mainContent = document.getElementById("main-content");
        if (mainContent) {
            mainContent.scrollIntoView({ behavior: 'auto', block: 'start' });
        } else {
            window.scrollTo(0, 0);
        }
    }, [pathname]);

    return null;
};

export default ScrollToTop;
