import React from "react";

export const BodyHomeTertiary = () => {

    return (
        <div className="container home-info">
            <div className="row d-flex justify-content-center">
                <h2>Contacto</h2>
                <hr className="hr-cart"></hr>
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center">
                        <div className="bg-info-icon">
                            <i className="my-3 info-icon fa-regular fa-map fa-2x"></i>
                        </div>
                        <h3 className="info-h3">Localización:</h3>
                        <p className="info-p">Ofic. Pedrera Alta 11, Ciudad Real</p>
                        <div className="alert alert-warning d-flex align-items-center" role="alert">
                            <svg
                                className="bi flex-shrink-0 me-2"
                                role="img"
                                aria-label="Warning:"
                                viewBox="0 0 16 16"
                                width="12"
                                height="12"
                                fill="currentColor"
                            >
                                <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z" />
                            </svg>
                            <div style={{ fontSize: "0.7rem" }}>
                                Actualmente la oficina no está abierta al público.
                            </div>
                        </div>
                    </div>
                </div>
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center"
                        onClick={() => window.location.href = 'mailto:admin@metalwolft.com'}>
                        <div className="bg-info-icon">
                            <i className="info-icon fa-solid fa-at fa-2x"></i>
                        </div>
                        <h3 className="info-h3">Email:</h3>
                        <p className="info-p">admin@metalwolft.com</p>
                    </div>
                </div>
                <div className="pt-4 px-4 col-12 col-sm-12 col-md-6 col-lg-4 col-xl-4">
                    <div className="home-info-card d-flex flex-column justify-content-center align-items-center"
                        onClick={() => window.location.href = 'tel:+34634112604'}>
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
