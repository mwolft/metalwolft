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
        path: path.resolve(__dirname, 'build'), // Carpeta de salida
        filename: 'static/js/[name].[contenthash].js', // Nombres con hash para cacheo
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
            filename: 'static/css/[name].[contenthash].css', // Nombres con hash para cacheo
        }),
        new Dotenv({
            safe: true,
            systemvars: true
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
        splitChunks: {
            chunks: 'all', // Divide el código en chunks
        }
    }
});
