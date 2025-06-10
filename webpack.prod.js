const { merge } = require('webpack-merge');
const path = require('path');
const common = require('./webpack.common.js');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const Dotenv = require('dotenv-webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = merge(common, {
    mode: 'production',
    output: {
        path: path.resolve(__dirname, 'build'),
        filename: '[name].[contenthash].js',
        publicPath: '/', 
    },
    module: {
        rules: [
            {
                test: /\.(css|scss)$/,
                use: [
                    MiniCssExtractPlugin.loader, 
                    'css-loader'
                ]
            }
        ]
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: 'styles.css',
        }),
        new Dotenv({
            systemvars: true,
            silent: true,
            path: null 
        }),
        new CopyWebpackPlugin({
            patterns: [
                { from: path.resolve(__dirname, 'public/_redirects'), to: path.resolve(__dirname, 'build') },
                { from: path.resolve(__dirname, 'public/robots.txt'), to: path.resolve(__dirname, 'build') },
                { from: path.resolve(__dirname, 'public/sitemap.xml'), to: path.resolve(__dirname, 'build') }
            ]
        })
    ],
    optimization: {
        minimize: true,
        minimizer: [
            new TerserPlugin({
                parallel: true,
            }),
            new CssMinimizerPlugin()
        ],
    }
});