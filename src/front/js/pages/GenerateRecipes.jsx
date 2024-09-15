import React, { useState, useContext } from 'react';
import { Context } from '../store/appContext';
import 'bootstrap/dist/css/bootstrap.min.css'; // Ensure Bootstrap is imported

export const GenerateRecipes = () => {
    const { store, actions } = useContext(Context);
    const [ingredientNames, setIngredientNames] = useState('');
    const [loading, setLoading] = useState(false);

    const handleGenerateRecipe = async () => {
        setLoading(true);
        await actions.generateRecipe(ingredientNames);
        setLoading(false);
    };

    const handleSaveToFavorites = async () => {
        if (store.generatedRecipe && store.recipeId) {
            await actions.addFavoriteRecipe(store.recipeId);
            alert("¡Receta añadida a favoritos!");
        }
        console.log(store.recipeId);
    };

    return (
        <div className="container-fluid" style={{ backgroundColor: '#D3D3D3', minHeight: '100vh', paddingBottom: '80px' }}>
            <div className="row justify-content-center mt-5">
                <div className="col-12 col-sm-10 col-md-8 col-lg-6">
                    <br />
                    <h2 className="text-center my-5">GENERE SU RECETA SALUDABLE</h2>
                    <input
                        type="text"
                        className="form-control mt-5"
                        placeholder="Ingrese ingredientes, por ej., pollo, brócoli, arroz"
                        value={ingredientNames}
                        onChange={(e) => setIngredientNames(e.target.value)}
                    />
                    <button onClick={handleGenerateRecipe} className="btn btn-warning mt-3 w-100">
                        {loading ? "Generando..." : "Generar Receta"}
                    </button>
                </div>
            </div>

            {store.generatedRecipe && (
                <div className="row justify-content-center mt-4">
                    <div className="col-12 col-sm-10 col-md-8 col-lg-6">
                        <div className="alert mt-3 recipe-container bg-warning-subtle text-dark p-4">
                            <h3 className="text-center mb-3">Receta Generada</h3>
                            <div dangerouslySetInnerHTML={{ __html: formatRecipe(store.generatedRecipe) }} />
                            <button onClick={handleSaveToFavorites} className="btn btn-warning mt-3 w-100">
                                Guardar en Favoritos
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {store.error && (
                <div className="row justify-content-center mt-3">
                    <div className="col-12 col-sm-10 col-md-8 col-lg-6">
                        <div className="alert alert-danger">
                            {store.error}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Updated formatRecipe function
const formatRecipe = (recipe) => {
    return recipe
        .replace(/\*\*(.*?)\*\*/g, '<h4>$1</h4>')  // Convert **Recipe Name** to <h4>
        .replace(/\*(.*?)\*/g, '<li>$1</li>')  // Convert * Ingredient to <li>
        .replace(/(\d+\.\s)/g, '<br /><strong>$1</strong>')  // Convert 1. Step to <br /><strong>
        .replace(/-\s/g, '• ')  // Convert * to bullet points
        .replace(/\n/g, '<br />')  // Convert newlines to <br />
        .replace(/Ingredients:/g, '<h5>Ingredientes:</h5>')  // "Ingredients:" to <h5>
        .replace(/Instructions:/g, '<h5>Instrucciones:</h5>')  // "Instructions:" to <h5>
        .replace(/Nutritional Information/g, '<h5>Información Nutricional</h5>');  // "Nutritional Information" to <h5>
};