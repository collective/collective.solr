var webpack = require("webpack");
var HtmlWebpackPlugin = require("html-webpack-plugin");

var config = {
  entry: "./src/index.jsx",
  output: {
    path: __dirname + "/dist",
    filename: "search.min.js"
  },
  module: {
    loaders: [
      {
        test: /\.jsx$/,
        loader: "babel",
        exclude: /node_modules/,
        query: {
          presets: ["env", "react"],
          plugins: ["transform-class-properties"]
        }
      },
      { test: /\.css$/, loaders: ["style", "css"] }
    ]
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "Webpack Starter React",
      template: "src/index.html",
      minify: {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        removeScriptTypeAttributes: true,
        removeStyleLinkTypeAttributes: true
      }
    })
  ],
  devServer: {
    contentBase: "./dist",
    port: 3000,
    colors: true,
    historyApiFallback: true,
    inline: true
  },
  devtool: "eval-source-map"
};

/*
 * If bundling for production, optimize output
 */
if (process.env.NODE_ENV === "production") {
  config.devtool = false;
  config.plugins = [
    new webpack.optimize.OccurenceOrderPlugin(),
    new webpack.optimize.UglifyJsPlugin({ comments: false }),
    new webpack.DefinePlugin({
      "process.env": { NODE_ENV: JSON.stringify("production") }
    })
  ];
}

module.exports = config;
