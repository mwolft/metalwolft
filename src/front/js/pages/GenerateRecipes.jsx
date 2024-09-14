import React, { useState, useContext } from 'react';
import { Context } from '../store/appContext';
import '../../styles/Recipe.css';

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
        <div style={{ backgroundColor: '#d3d3d3', height: '100vh' }}>
            <div className='row'>
                <div className='container mt-5'>
                </div>
                <div className="container my-5">
                    <div className='mx-3'>
                        <h2 style={{ color: 'black', marginBottom: '20px' }}>GENERE SU RECETA SALUDABLE</h2>
                    </div>
                    <div className="mx-3">
                        <input
                            type="text"
                            className="form-control"
                            placeholder="Ingrese ingredientes, por ej., pollo, brócoli, arroz"
                            value={ingredientNames}
                            onChange={(e) => setIngredientNames(e.target.value)}
                        />
                        <button onClick={handleGenerateRecipe} className="btn btn-warning mt-3">
                            {loading ? "Generando..." : "Generar Receta"}
                        </button>
                    </div>
                    {store.generatedRecipe && (
                        <div className="d-flex justify-content-center">
                            <div className="alert mt-3 recipe-container" style={{ backgroundColor: '#FFFACD', color: 'black', maxWidth: '800px', width: '100%' }}>
                                <h3 className="text-center" style={{ marginBottom: '20px' }}>Receta Generada</h3>
                                <div dangerouslySetInnerHTML={{ __html: formatRecipe(store.generatedRecipe) }} />
                                <button onClick={handleSaveToFavorites} className="btn btn-warning mt-3 w-100">Guardar en Favoritos</button>
                            </div>
                        </div>
                    )}
                    {store.error && (
                        <div className="alert alert-danger mt-3">
                            {store.error}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// Updated formatRecipe function (CSS applied via Recipe.css)
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