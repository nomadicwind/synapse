module.exports = function(api) {
  // Check environment before caching
  const isTest = api.env('test');
  api.cache(true);
  
  return {
    presets: [
      [
        'babel-preset-expo',
        isTest ? {} : {
          'jsxImportSource': 'nativewind'
        }
      ]
    ],
    plugins: [
      [
        'module:react-native-dotenv',
        {
          'moduleName': '@env',
          'path': '.env'
        }
      ],
      [
        'react-native-reanimated/plugin',
        {
          'globals': ['__scanQR'],
          'relativeSourceLocation': true
        }
      ]
    ]
  };
};
