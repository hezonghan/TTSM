
const path = require('path');

// const VueLoaderPlugin = require('vue-loader/lib/plugin');
// const VueLoaderPlugin = require('vue-loader/lib/plugin-webpack5');
const { VueLoaderPlugin } = require('vue-loader');

module.exports = {
    entry: "./frontend/index.js",
    output: {
        path: path.resolve(__dirname , 'frontend'),
        filename: 'index_bundle.js'
    },
    module: {
        rules: [
            {
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.css$/,
                use:['style-loader','css-loader']
            },
        ]
    },
    plugins: [
        new VueLoaderPlugin()
    ],
    // mode: 'production'
    mode: 'development'
}
