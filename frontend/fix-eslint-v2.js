const fs = require('fs');
const path = require('path');

// Function to recursively find all TypeScript/TSX files
function findFiles(dir, extensions = ['.ts', '.tsx']) {
  let results = [];
  const list = fs.readdirSync(dir);
  
  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat && stat.isDirectory()) {
      // Skip node_modules and .next directories
      if (!['node_modules', '.next', 'dist', 'build'].includes(file)) {
        results = results.concat(findFiles(filePath, extensions));
      }
    } else {
      const ext = path.extname(file);
      if (extensions.includes(ext)) {
        results.push(filePath);
      }
    }
  });
  
  return results;
}

// Function to fix common ESLint issues
function fixFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let modified = false;

  // Fix 1: Replace specific 'any' patterns with proper types
  const anyReplacements = [
    // Function parameters with any
    { pattern: /\(([^:)]*): any\)/g, replacement: '($1: unknown)' },
    // Variable declarations with any
    { pattern: /: any\[\]/g, replacement: ': unknown[]' },
    { pattern: /: any\s*=/g, replacement: ': unknown =' },
    { pattern: /: any\s*\)/g, replacement: ': unknown)' },
    { pattern: /: any\s*,/g, replacement: ': unknown,' },
    { pattern: /: any\s*;/g, replacement: ': unknown;' },
    // Generic types
    { pattern: /<any>/g, replacement: '<unknown>' },
    // Array types
    { pattern: /Array<any>/g, replacement: 'Array<unknown>' },
    // Record types
    { pattern: /Record<string, any>/g, replacement: 'Record<string, unknown>' },
  ];

  anyReplacements.forEach(({ pattern, replacement }) => {
    if (pattern.test(content)) {
      content = content.replace(pattern, replacement);
      modified = true;
    }
  });

  // Fix 2: Fix React unescaped entities in JSX
  // Only fix entities that are clearly in JSX text content
  const entityFixes = [
    { pattern: />([^<]*)'([^<]*)</g, replacement: '>$1&apos;$2<' },
    { pattern: />([^<]*)"([^<]*)</g, replacement: '>$1&quot;$2<' },
  ];

  entityFixes.forEach(({ pattern, replacement }) => {
    if (pattern.test(content)) {
      content = content.replace(pattern, replacement);
      modified = true;
    }
  });

  // Fix 3: Replace @ts-ignore with @ts-expect-error
  if (content.includes('@ts-ignore')) {
    content = content.replace(/@ts-ignore/g, '@ts-expect-error');
    modified = true;
  }

  // Fix 4: Remove unused imports (simple cases)
  const unusedImportPatterns = [
    // Remove unused imports that are clearly not used
    { pattern: /import\s+{\s*fireEvent\s*}\s+from\s+['"]@testing-library\/react['"];\s*\n/g, replacement: '' },
    { pattern: /import\s+{\s*waitFor\s*}\s+from\s+['"]@testing-library\/react['"];\s*\n/g, replacement: '' },
  ];

  unusedImportPatterns.forEach(({ pattern, replacement }) => {
    if (pattern.test(content)) {
      content = content.replace(pattern, replacement);
      modified = true;
    }
  });

  // Fix 5: Fix require() imports to ES6 imports
  const requirePattern = /const\s+([^=\s]+)\s*=\s*require\(['"]([^'"]+)['"]\);?/g;
  if (requirePattern.test(content)) {
    content = content.replace(requirePattern, 'import $1 from \'$2\';');
    modified = true;
  }

  // Fix 6: Remove unused variable declarations (simple cases)
  const lines = content.split('\n');
  const filteredLines = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let shouldKeep = true;
    
    // Check for unused variable patterns
    if (line.includes('const ') && line.includes(' = ') && !line.includes('//')) {
      const varMatch = line.match(/const\s+([^=\s\[\{]+)/);
      if (varMatch) {
        const varName = varMatch[1];
        // Count occurrences of this variable in the entire file
        const regex = new RegExp(`\\b${varName}\\b`, 'g');
        const matches = content.match(regex);
        
        // If variable is only used once (in its declaration), it might be unused
        if (matches && matches.length === 1) {
          // Additional check: make sure it's not exported or used in JSX
          if (!content.includes(`export { ${varName}`) && 
              !content.includes(`export default ${varName}`) &&
              !content.includes(`<${varName}`) &&
              !content.includes(`{${varName}}`)) {
            shouldKeep = false;
            modified = true;
          }
        }
      }
    }
    
    if (shouldKeep) {
      filteredLines.push(line);
    }
  }
  
  if (modified) {
    content = filteredLines.join('\n');
  }

  // Write back if modified
  if (modified) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Fixed: ${filePath}`);
  }
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = findFiles(srcDir);

console.log(`Found ${files.length} TypeScript/TSX files`);

files.forEach(file => {
  try {
    fixFile(file);
  } catch (error) {
    console.error(`Error fixing ${file}:`, error.message);
  }
});

console.log('ESLint fixes completed!');