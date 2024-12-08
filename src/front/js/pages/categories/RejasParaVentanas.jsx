import React, { useEffect, useContext, useState } from "react";
import { Helmet } from "react-helmet";
import { Breadcrumb } from "../../component/Breadcrumb.jsx";
import { Product } from "../../component/Product.jsx";
import { AsideCategories } from "../../component/AsideCategories.jsx";
import { AsideOthersCategories } from "../../component/AsideOthersCategories.jsx";
import { AsidePost } from "../../component/AsidePost.jsx";
import { Context } from "../../store/appContext.js";
import "../../../styles/categories-pages.css";
import { Link } from "react-router-dom";

export const RejasParaVentanas = () => {
    const { store, actions } = useContext(Context);
    const rejasCategoryId = 1;
    const [selectedCategoryId, setSelectedCategoryId] = useState(rejasCategoryId);
    const [selectedSubcategoryId, setSelectedSubcategoryId] = useState(null);
    const [metaData, setMetaData] = useState({}); 

    useEffect(() => {
        actions.fetchProducts(selectedCategoryId, selectedSubcategoryId);
    }, [selectedCategoryId, selectedSubcategoryId]);

    useEffect(() => {
        fetch("/api/seo/rejas-para-ventanas")
            .then((response) => response.json())
            .then((data) => setMetaData(data));
    }, []);

    const handleCategorySelect = (categoryId) => {
        setSelectedCategoryId(categoryId);
        setSelectedSubcategoryId(null);
    };

    const handleSubcategorySelect = (subcategoryId) => {
        setSelectedSubcategoryId(subcategoryId);
    };

    return (
        <>
            <Helmet>
                <title>{metaData.title}</title>
                <meta name="description" content={metaData.description} />
                <meta name="keywords" content={metaData.keywords} />
                <meta property="og:image" content={metaData.og_image} />
                <meta property="og:url" content={metaData.og_url} />
                {metaData.json_ld && (
                    <script type="application/ld+json">
                        {JSON.stringify(metaData.json_ld)}
                    </script>
                )}
            </Helmet>
            <Breadcrumb />
            <div className="container">
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                        <AsideCategories
                            onSelectCategory={handleCategorySelect}
                            onSelectSubcategory={handleSubcategorySelect}
                            categoryId={rejasCategoryId}
                        />
                        <div className="d-none d-lg-block">
                            <AsidePost />
                            <AsideOthersCategories currentCategoryId={rejasCategoryId} />
                        </div>
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2">
                        <div className="row">
                            {store.products && store.products.length > 0 ? (
                                store.products.map((product, index) => (
                                    <div key={index} className="col-6 col-sm-6 col-md-4 col-lg-4 col-xl-4 mb-4 d-flex">
                                        <Product product={product} className="w-100" />
                                    </div>
                                ))
                            ) : (
                                <p>Cargando productos o no hay productos disponibles para esta categoría.</p>
                            )}
                        </div>
                    </div>
                    <div className="col-12 d-block d-lg-none order-3">
                        <AsidePost />
                        <AsideOthersCategories currentCategoryId={rejasCategoryId} />
                    </div>
                </div>
                <div className="row">
                    <div className="col-12 col-lg-3 col-xl-3 order-1">
                    </div>
                    <div className="col-12 col-lg-9 col-xl-9 order-2 my-4">
                    <p>Las <strong>rejas para ventanas</strong> son elementos esenciales en cualquier hogar. En esta página, exploraremos cómo estas <strong>rejas para ventanas modernas</strong> no solo brindan <b>seguridad y protección</b>, sino que también pueden ser una expresión de <b>estilo y diseño</b> en nuestro catálogo exclusivo online.</p>
                        <p>Nuestra gama se basa en la premisa de que no deberías tener que sacrificar el estilo en post de la seguridad. En cada detalle encontrarás una cuidadosa planificación y ejecución de nuestras <strong>rejas para ventanas sencillas y bonitas</strong>.</p>
                        <p>Descubre nuestra amplia gama de <strong>rejas para ventanas sin obra y con obra</strong> que combinan <b>funcionalidad y estética</b>, garantizando la seguridad de tu hogar sin comprometer su apariencia.</p>
                        <br />
                        <h2>REJAS PARA VENTANAS SENCILLAS Y BONITAS</h2>
                        <hr className="hr-cart" />
                        <img className="img-fluid my-2" style={{ width: '100%', height: 'auto' }} src="https://res.cloudinary.com/dewanllxn/image/upload/v1733674435/rejas-para-ventanas-sencillas-y-bonitas_ue4qzc.avif" alt="rejas para ventanas" />
                        <p>Las <strong>rejas para ventanas sencillas y bonitas </strong>tienen una creciente demanda en la actualidad y destacan por su <b>simplicidad y belleza</b>.</p>
                        <p>Unos años atrás se han destacado por la combinación de figuras metálicas, un enfoque que está cayendo en desuso.</p>
                        <p>En la actualidad, la demanda de rejas online se caracteriza por una estética más simplificada y atractiva, reduciendo la cantidad de material empleado sin comprometer la <b>modernidad de su diseño.</b></p>
                        <br />
                        <h2>REJAS PARA VENTANAS MODERNAS</h2>
                        <hr className="hr-cart" />
                        <p>Las <strong>rejas para ventanas modernas</strong> han experimentado una transformación en su <b>estilo y materiales</b>, siguiendo líneas más <strong>sencillas</strong> siendo igual de bonitas, ofreciendo un equilibrio perfecto entre <b>seguridad y estética</b>.</p>
                        <p>Aunque el <strong>hierro</strong> sigue siendo el material predominante, se han incorporado otros materiales, como el acero inoxidable, para satisfacer las necesidades cambiantes de los propietarios.</p>
                        <p>En Metal Wolf, nos enorgullece presentar una selección de <strong>rejas para ventanas modernas</strong> que destacan tanto por su estilo como por su capacidad de brindar protección efectiva.</p>
                        <p>Nuestra filosofía se centra en la creación de diseños que no solo cumplen con su propósito principal, sino que también realzan la estética de su hogar.</p>
                        <br />
                        <h2>REJAS PARA VENTANAS SIN OBRA</h2>
                        <hr className="hr-cart" />
                        <img className="img-fluid my-2" style={{ width: '100%', height: 'auto' }} src="https://res.cloudinary.com/dewanllxn/image/upload/v1733674435/rejas-para-ventanas-modernas-2023_ifvzpo.avif" alt="rejas para ventanas sencillas y bonitas" />
                        <p>Nuestras <strong>rejas para ventanas</strong> están especialmente diseñadas para adaptarse a huecos de ventana <strong>sin obra</strong>, es decir, sin la necesidad de realizar costosos trabajos de albañilería.</p>
                        <p>Este tipo de instalación no solo conserva la seguridad de su propiedad, gracias a la utilización de tornillos especiales tipo Torx inviolables (incluidos), sino que también simplifica el proceso de montaje, lo que a su vez se traduce en el <strong>precio</strong>.</p>
                        <p>Tenemos un artículo dedicado exclusivamente a <Link to="/instalation-rejas-para-ventanas" style={{ color: '#ff324d', textDecoration: 'underline', fontStyle: 'italic' }}>¿cómo instalar rejas para ventanas?</Link></p>
                        <video controls preload="auto" style={{ width: '100%', height: 'auto' }}>
                            <source src="https://res.cloudinary.com/dewanllxn/video/upload/v1733563618/instalacion-rejas-para-ventanas_kcno5b.webm" type="video/webm" />
                        </video>                    
                        </div>
                </div>
            </div>
        </>
    );
};
