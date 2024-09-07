import React, { useState, useContext } from 'react';
import { Context } from '../store/appContext';

export const GenerateRecipes = () => {
    const { store, actions } = useContext(Context);
    const [ingredientNames, setIngredientNames] = useState('');
    const [loading, setLoading] = useState(false);

    // Function to generate recipe
    const handleGenerateRecipe = async () => {
        setLoading(true);
        await actions.generateRecipe(ingredientNames);
        setLoading(false);
    };

    // Function to save recipe to favorites
    const handleSaveToFavorites = async () => {
        if (store.generatedRecipe && store.recipeId) {
            await actions.addFavoriteRecipe(store.recipeId);  // Save to favorites
            alert("Recipe added to favorites!");  // Simple feedback
        }
        console.log(store.recipeId);
    };

    return (
        <div className="container my-5">
            <h2>Generate a Healthy Recipe</h2>
            <div className="mb-3">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Enter ingredients, e.g., chicken, broccoli, rice"
                    value={ingredientNames}
                    onChange={(e) => setIngredientNames(e.target.value)}
                />
                <button onClick={handleGenerateRecipe} className="btn btn-primary mt-3">
                    {loading ? "Generating..." : "Generate Recipe"}
                </button>
            </div>
            {store.generatedRecipe && (
                <div className="alert alert-success mt-3">
                    <h3>Generated Recipe</h3>
                    <div className="recipe-container" dangerouslySetInnerHTML={{ __html: formatRecipe(store.generatedRecipe) }} />
                    <button onClick={handleSaveToFavorites} className="btn btn-warning mt-3">Save to Favorites</button>
                </div>
            )}
            {store.error && (
                <div className="alert alert-danger mt-3">
                    {store.error}
                </div>
            )}
        </div>
    );
};
// Function to format the recipe
const formatRecipe = (recipe) => {
    return recipe
        .replace(/\*\*(.*?)\*\*/g, '<h4>$1</h4>')  // Convert **Recipe Name** to <h4>Recipe Name</h4>
        .replace(/\*(.*?)\*/g, '<li>$1</li>')  // Convert * Ingredient to <li>Ingredient</li>
        .replace(/(\d+\.\s)/g, '<br /><strong>$1</strong>')  // Convert 1. Step to <br /><strong>1. Step</strong>
        .replace(/-\s/g, '• ')  // Convert * to bullet points
        .replace(/\n/g, '<br />')  // Convert newlines to <br />
        .replace(/Ingredients:/g, '<h5>Ingredients:</h5>')  // Convert "Ingredients:" to a header
        .replace(/Instructions:/g, '<h5>Instructions:</h5>')  // Convert "Instructions:" to a header
        .replace(/Nutritional Information/g, '<h5>Nutritional Information</h5>');  // Convert "Nutritional Information" to a header
};