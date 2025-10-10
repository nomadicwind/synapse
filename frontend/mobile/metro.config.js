const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add web-specific configuration
config.resolver.sourceExts.push('web.js', 'web.ts', 'web.tsx');

// Configure ES modules for web
config.transformer.getTransformOptions = async () => ({
  transform: {
    experimentalImportSupport: false,
    inlineRequires: true,
  },
});

// Add web-specific resolver options
config.resolver = {
  ...config.resolver,
  resolverMainFields: ['browser', 'module', 'main'],
};

module.exports = config;
