const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const Dotenv = require('dotenv-webpack');

module.exports = {
  entry: './src/front/js/index.js',
  output: {
    filename: 'static/js/[name].[contenthash].js', // Incluye hash para cacheo
    path: path.resolve(__dirname, 'build'), // Directorio de salida
    publicPath: '/' // Raíz para servir los archivos
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
      {
        test: /\.(css|scss)$/,
        use: [
          'style-loader', // Cambiar a MiniCssExtractPlugin.loader en prod
          'css-loader'
        ]
      },
      {
        test: /\.(png|svg|jpg|gif|jpeg|webp|avif)$/i,
        type: 'asset/resource', // Reemplaza file-loader para Webpack 5
      },
      {
        test: /\.(woff|woff2|ttf|eot|svg)$/,
        type: 'asset/resource'
      }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx']
  },
  plugins: [
    new HtmlWebpackPlugin({
      favicon: 'favicon.ico',
      template: 'template.html',
      filename: 'index.html'
    }),
    new Dotenv({ safe: true, systemvars: true })
  ]
};
