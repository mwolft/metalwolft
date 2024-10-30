import React from "react";
import "../../styles/categories-pages.css";

export const AsidePost = () => {

    return (
        <div className="widget my-5">
            <h5 className="widget_title">Post Recientes</h5>
            <hr className="hr-home" />
            <div className="others-categories">
                <img className="img-other-categories" src="https://www.metalwolft.com/assets/images/blog/rejas-para-ventanas.avif" alt="" />
                <p className="p-other-categories">5 Consejos para Medir el Espacio de tus Rejas para Ventanas <br /><span className="other-categories-span">16 de marzo del 2023</span></p>
            </div>
            <div className="others-categories">
                <img className="img-other-categories" src="https://www.metalwolft.com/assets/images/blog/rejas-de-seguridad-para-ventanas.avif" alt="" />
                <p className="p-other-categories">Instalación Sin Obra: Rejas para Ventanas con Tornillos Torx<br /><span className="other-categories-span">16 de marzo del 2023</span></p>
            </div>
        </div>
    );
};
