import React from "react";
import "../../styles/categories-pages.css";

export const AsideOthersCategories = () => {

    return (
        <div className="widget my-5">
            <h5 className="widget_title">Otras Categorías</h5>
            <hr className="hr-home" />
            <div className="others-categories">
                <img className="img-other-categories" src="https://www.metalwolft.com/assets/images/vallados-metalicos/geelong/vallado-metalico.avif" alt="" />
                <p className="p-other-categories">Vallados Metálicos <br /><button className="buton-other-categories">Ir a categoría</button></p>
            </div>
            <div className="others-categories">
                <img className="img-other-categories" src="https://www.metalwolft.com/assets/images/vallados-metalicos/geelong/vallado-metalico.avif" alt="" />
                <p className="p-other-categories">Vallados Metálicos <br /><button className="buton-other-categories">Ir a categoría</button></p>
            </div>
            <div className="others-categories">
                <img className="img-other-categories" src="https://www.metalwolft.com/assets/images/vallados-metalicos/geelong/vallado-metalico.avif" alt="" />
                <p className="p-other-categories">Vallados Metálicos <br /><button className="buton-other-categories">Ir a categoría</button></p>
            </div>
        </div>
    );
};
