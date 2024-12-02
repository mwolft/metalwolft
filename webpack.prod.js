const { merge } = require('webpack-merge');
const path = require('path');
const common = require('./webpack.common.js');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const Dotenv = require('dotenv-webpack');

module.exports = merge(common, {
    mode: 'production',
    output: {
        path: path.resolve(__dirname, 'public'), // Generar archivos directamente en public
        filename: 'bundle.js', // Generar el archivo bundle.js
        publicPath: '/' // Sirve desde la raíz
    },
    module: {
        rules: [
            {
                test: /\.(css|scss)$/,
                use: [
                    MiniCssExtractPlugin.loader, // Extrae CSS en archivos
                    'css-loader'
                ]
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: 'styles.css', // Generar un único archivo CSS
        }),
        new Dotenv({
            systemvars: true, // Carga variables de entorno del sistema
            silent: true // Suprime advertencias si faltan variables
        })
    ],
    optimization: {
        minimize: true, // Activa la minimización
        minimizer: [
            new TerserPlugin({
                parallel: true, // Paraleliza la minificación JS
            }),
            new CssMinimizerPlugin() // Minimiza CSS
        ],
    }
});
