import React from "react";

export const BodyHomeTertiary = () => {

    return (
        <div className="container home-info">
            <div className="row d-flex justify-content-center">
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center">
                        <div className="bg-info-icon">
                            <i className="my-3 info-icon fa-regular fa-map fa-2x"></i>
                        </div>
                        <h3 className="info-h3">Localización:</h3>
                        <p className="info-p">Ofic. Pedrera Alta 11, Ciudad Real.</p>
                    </div>
                </div>
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center">
                        <div className="bg-info-icon">
                            <i className="info-icon fa-solid fa-at fa-2x"></i>
                        </div>
                        <h3 className="info-h3">Email:</h3>
                        <p className="info-p">admin@metalwolft.com</p>
                    </div>
                </div>
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center">
                        <div className="bg-info-icon">
                            <i className="info-icon fa-solid fa-phone-volume fa-2x"></i>
                        </div>
                        <h3 className="info-h3">Teléfono:</h3>
                        <p className="info-p">+34 634112604</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

